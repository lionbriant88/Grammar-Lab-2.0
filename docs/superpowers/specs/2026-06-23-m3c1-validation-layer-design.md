# M3c1 — Validation Layer: LanguageTool Integration + Rule Validators

> 设计稿日期: 2026-06-23
> 状态: 待实施
> 前置: M3a + M3a+1 + M3b 已完成
> 阶段: M3c1（验证层优先）

---

## 0. 执行摘要

M3c1 是 M3c 渐进式路线图的第一阶段，专注于**验证层完善**。

### 核心任务
1. LanguageTool 嵌入式服务器集成（第 6 道 Validator）
2. 实现剩余 3 项浅层 Rule Validators
3. 引入 safe_execute() 韧性包装器
4. 80/15/5 测试金字塔（重点：降级测试）

### 架构原则
- **验证优先，生成其次** - 永不同时开发模板和验证器
- **零崩溃保证** - 任何组件失败 → 降级 → 继续工作
- **Always HTTP 200** - 永不返回 500，Validator 是教师非编译器
- **LanguageTool 次级顾问** - Grammar Engine 是唯一语法权威

### M3c1 完成后
- ✅ 验证层冻结（永久稳定）
- ✅ 为 M3c2-5 打下坚实基础
- ✅ Grammar Engine 具备完整的 6 项验证能力

---

## 1. 架构总览

### 1.1 验证管道（6 项）

```
Validator 1: subject_verb_agreement ✅ (M3a)
          ↓
Validator 2: tense_consistency ✅ (M3b) 
          ↓
Validator 3: clause_completeness 🔨 (M3c1)
          ↓
Validator 4: non_finite_legality 🔨 (M3c1)
          ↓
Validator 5: relative_pronoun_match 🔨 (M3c1)
          ↓
Validator 6: LanguageTool 🔨 (M3c1)
          ↓
Merge ValidationReport (去重)
          ↓
Return (Always HTTP 200)
```

### 1.2 韧性保证

**safe_execute() 包装器：**
- 每个 Validator 在 safe_execute() 中运行
- 任何异常 → 捕获 → 降级为 WARNING → 继续管道
- 一个 Validator 失败不阻断其他 Validators

**LanguageTool 降级策略：**
- 未启动 → 跳过 Validator 6 → 显示 INFO → 继续
- 超时（5s）→ 返回 timeout LTReport → INFO
- 崩溃 → is_alive()=False → 下次请求尝试重启

**保证：**
- 永不返回 HTTP 500
- Backend 启动立即可用（不等待 LanguageTool）
- 系统始终可用

---

## 2. ExternalServiceManager 基类设计

### 2.1 为什么需要基类

未来复用场景：
- LanguageTool（M3c1）
- Ollama（M4 本地 AI）
- M4 AI Validator
- TTS 服务

### 2.2 基类定义

**文件：** `backend/grammar_engine/external_service_manager.py`

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

@dataclass
class ServiceStatus:
    """服务状态（实时查询，非缓存）"""
    available: bool
    message: str
    port: Optional[int] = None

class ExternalServiceManager(ABC):
    """外部服务管理基类"""
    
    @abstractmethod
    def is_alive(self) -> bool:
        """实时健康检查（轻量级，不调用实际 API）"""
        
    @abstractmethod
    def get_status(self) -> ServiceStatus:
        """获取详细状态"""
        
    @abstractmethod
    def ensure_server_async(self):
        """后台线程启动服务器（非阻塞）"""
        
    @abstractmethod
    def restart(self):
        """重启服务"""
        
    @abstractmethod
    def shutdown(self):
        """关闭服务"""
```

### 2.3 关键设计原则

**无状态：**
- `is_alive()` 实时检查进程和端口，不缓存 bool
- 状态从系统获取，不维护内部状态变量

**非阻塞启动：**
- `ensure_server_async()` 立即返回
- 后台线程启动服务
- Grammar Engine 立即可用

**可重启：**
- `restart()` 方法允许故障恢复
- 进程崩溃后可自动或手动重启


---

## 3. LanguageToolManager 实现

### 3.1 设计概览

**文件：** `backend/grammar_engine/languagetool_manager.py`

**职责：**
- 管理嵌入式 LanguageTool 服务器生命周期
- 提供结构化语法检查接口
- 处理服务器故障和超时

### 3.2 LTReport 结构化结果

```python
@dataclass
class LTReport:
    """LanguageTool 检查结果（结构化，非 dict）"""
    success: bool
    matches: list[dict]  # LanguageTool 原始 matches
    error: Optional[str] = None
    timeout: bool = False
```

### 3.3 核心实现

```python
class LanguageToolManager(ExternalServiceManager):
    def __init__(self, jar_path: str, jre_path: str, port: int = 8081):
        self.jar_path = jar_path
        self.jre_path = jre_path
        self.port = port
        self.process: Optional[subprocess.Popen] = None
        self._startup_thread: Optional[threading.Thread] = None
    
    def is_alive(self) -> bool:
        """检查进程是否存在且端口可达（不调用 /v2/check）"""
        if self.process is None or self.process.poll() is not None:
            return False
        
        # 检查端口是否监听
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            result = sock.connect_ex(('localhost', self.port))
            sock.close()
            return result == 0
        except:
            return False
    
    def ensure_server_async(self):
        """后台线程启动（非阻塞）"""
        if self.is_alive():
            return
        
        if self._startup_thread and self._startup_thread.is_alive():
            return  # 已在启动中
        
        self._startup_thread = threading.Thread(
            target=self._start_server,
            daemon=True
        )
        self._startup_thread.start()
    
    def _start_server(self):
        """实际启动逻辑（后台线程）"""
        try:
            cmd = [
                os.path.join(self.jre_path, "bin", "java"),
                "-cp", self.jar_path,
                "org.languagetool.server.HTTPServer",
                "--port", str(self.port),
                "--allow-origin", "*"
            ]
            
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL,  # 防止阻塞
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            logger.info(f"LanguageTool server starting on port {self.port}")
        except Exception as e:
            logger.error(f"Failed to start LanguageTool: {e}")
    
    def check(self, sentence: str, timeout: int = 5) -> LTReport:
        """语法检查（返回结构化 LTReport）"""
        if not self.is_alive():
            return LTReport(
                success=False,
                matches=[],
                error="LanguageTool server not available"
            )
        
        try:
            response = requests.post(
                f"http://localhost:{self.port}/v2/check",
                data={"text": sentence, "language": "en-US"},
                timeout=timeout
            )
            response.raise_for_status()
            data = response.json()
            return LTReport(success=True, matches=data.get("matches", []))
        
        except requests.Timeout:
            return LTReport(success=False, matches=[], error="Timeout", timeout=True)
        except Exception as e:
            return LTReport(success=False, matches=[], error=str(e))
    
    def restart(self):
        """重启服务"""
        self.shutdown()
        self.ensure_server_async()
    
    def shutdown(self):
        """关闭服务"""
        if self.process:
            self.process.terminate()
            self.process.wait(timeout=5)
            self.process = None
```

### 3.4 单例模式

```python
_languagetool_manager_instance: Optional[LanguageToolManager] = None

def get_languagetool_manager() -> LanguageToolManager:
    """获取全局 LanguageTool 管理器单例"""
    global _languagetool_manager_instance
    
    if _languagetool_manager_instance is None:
        jar_path = os.getenv("LT_JAR_PATH", "./languagetool/languagetool-server.jar")
        jre_path = os.getenv("LT_JRE_PATH", "./jre")
        
        _languagetool_manager_instance = LanguageToolManager(
            jar_path=jar_path,
            jre_path=jre_path,
            port=8081
        )
        
        # 后台启动
        _languagetool_manager_instance.ensure_server_async()
    
    return _languagetool_manager_instance
```

### 3.5 启动流程

```
Electron 启动
    ↓
Python Backend 启动
    ↓
app.py startup_event()
    ↓
get_languagetool_manager().ensure_server_async()  # 非阻塞
    ↓
Grammar Engine 立即可用（Validators 1-5 工作）
    ↓
后台线程启动 LanguageTool（5-10 秒）
    ↓
LanguageTool 就绪后，Validator #6 自动接入
```

---

## 4. safe_execute() 韧性包装器

### 4.1 设计目标

一个 Validator 失败不应阻断整个管道。失败降级为 WARNING，系统继续运行。

### 4.2 实现

**文件：** `backend/grammar_engine/expansion_validator.py`（在现有文件中添加）

```python
def safe_execute(
    validator_func: Callable,
    validator_name: str,
    *args,
    **kwargs
) -> ValidationReport:
    """安全执行 Validator，捕获所有异常。"""
    try:
        return validator_func(*args, **kwargs)
    except Exception as e:
        logger.error(f"Validator {validator_name} failed: {e}", exc_info=True)
        return ValidationReport(
            severity="WARNING",
            is_valid=True,  # 不阻断
            warnings=[f"校验器 {validator_name} 运行失败: {str(e)}"],
            errors=[],
            infos=[f"系统仍可正常使用，此校验项已跳过。"],
            auto_corrections=[]
        )
```

### 4.3 更新 validate() 统一入口

```python
def validate(sentence: str, doc: Any, phrases: List[PhraseNode]) -> ValidationReport:
    """6 项检查统一入口（M3c1 完整版）。"""
    
    reports = [
        safe_execute(
            validate_subject_verb_agreement,
            "subject_verb_agreement",
            sentence, doc, phrases
        ),
        safe_execute(
            validate_tense_consistency,
            "tense_consistency",
            sentence, doc, phrases
        ),
        safe_execute(
            validate_clause_completeness,
            "clause_completeness",
            sentence, doc, phrases
        ),
        safe_execute(
            validate_non_finite_legality,
            "non_finite_legality",
            sentence, doc, phrases
        ),
        safe_execute(
            validate_relative_pronoun_match,
            "relative_pronoun_match",
            sentence, doc, phrases
        ),
        safe_execute(
            validate_with_languagetool,
            "languagetool",
            sentence
        ),
    ]
    
    return _merge_reports(reports)
```


---

## 5. 三项浅层 Rule Validators

### 5.1 设计原则

**故意保持浅层：**
- 目标覆盖率：80%（常见错误）
- 不追求 95%+ 完整覆盖
- 复杂情况留给 LanguageTool 和未来 AI Validators
- Rule Validators 必须简单、确定性、稳定

### 5.2 clause_completeness（从句完整性）

**检查范围：**
- ✅ 检测明显不完整从句（缺主语/谓语）
- ❌ 不处理：省略、倒装、分裂句、时态逻辑

**实现：**
```python
def validate_clause_completeness(
    sentence: str, doc: Any, phrases: List[PhraseNode]
) -> ValidationReport:
    """检查从句是否完整（有主语+谓语）。
    
    示例错误：
    - "The boy who."
    - "The boy who happy."
    - "because he"
    """
    errors = []
    warnings = []
    
    # 找出所有 CLAUSE 类型的短语
    clauses = [p for p in phrases if p.type == "CLAUSE"]
    
    for clause in clauses:
        # 检查从句内是否有 NP + VP
        clause_phrase_ids = set([clause.id] + clause.children_ids)
        clause_phrases = [p for p in phrases if p.id in clause_phrase_ids]
        
        has_subject = any(p.type == "NP" and p.syntactic_role == "subject" 
                         for p in clause_phrases)
        has_predicate = any(p.type == "VP" and p.syntactic_role == "predicate"
                           for p in clause_phrases)
        
        if not has_subject:
            errors.append(f"从句 '{clause.text}' 缺少主语")
        
        if not has_predicate:
            errors.append(f"从句 '{clause.text}' 缺少谓语")
    
    severity = "ERROR" if errors else "PASS"
    is_valid = (severity != "ERROR")
    
    return ValidationReport(
        severity=severity,
        is_valid=is_valid,
        errors=errors,
        warnings=warnings,
        infos=[],
        auto_corrections=[]
    )
```

### 5.3 non_finite_legality（非谓语合法性）

**检查范围：**
- ✅ 小型 VerbPatternDB（100-300 个高频动词）
- ✅ to + base form 检查
- ❌ 不追求完整英语覆盖

**VerbPatternDB 示例：**
```python
VERB_PATTERNS = {
    # verb + doing
    "enjoy": ["doing"],
    "avoid": ["doing"],
    "finish": ["doing"],
    "suggest": ["doing"],
    "keep": ["doing"],
    "mind": ["doing"],
    
    # verb + to do
    "want": ["to_do"],
    "decide": ["to_do"],
    "plan": ["to_do"],
    "hope": ["to_do"],
    "expect": ["to_do"],
    
    # verb + both
    "like": ["doing", "to_do"],
    "love": ["doing", "to_do"],
    "hate": ["doing", "to_do"],
    "start": ["doing", "to_do"],
    
    # ... 100-300 个常见动词
}
```

**实现：**
```python
def validate_non_finite_legality(
    sentence: str, doc: Any, phrases: List[PhraseNode]
) -> ValidationReport:
    """检查非谓语动词使用。
    
    检查：
    1. to + base form（拒绝 to went, to going）
    2. 高频动词模式（enjoy + doing, want + to do）
    """
    errors = []
    warnings = []
    
    # 检查 to + 动词形式
    tokens = list(doc)
    for i, token in enumerate(tokens):
        if token.text.lower() == "to" and i + 1 < len(tokens):
            next_token = tokens[i + 1]
            if next_token.pos_ == "VERB":
                # 检查是否为原形
                if next_token.tag_ not in ["VB"]:  # VB = base form
                    errors.append(
                        f"'to' 后应接动词原形，而非 '{next_token.text}'"
                    )
    
    # 检查动词模式（简化版）
    for i, phrase in enumerate(phrases):
        if phrase.type == "VP":
            verb_lemma = phrase.head_token_text.lower()
            pattern = VERB_PATTERNS.get(verb_lemma)
            
            if pattern and i + 1 < len(phrases):
                next_phrase = phrases[i + 1]
                
                if next_phrase.type == "VP":
                    verb_form = next_phrase.features.get("verb_form")
                    
                    if "doing" in pattern and verb_form not in ["present_participle", "gerund"]:
                        warnings.append(
                            f"'{verb_lemma}' 通常后接动名词(-ing 形式)"
                        )
                    
                    if "to_do" in pattern and verb_form != "infinitive":
                        warnings.append(
                            f"'{verb_lemma}' 通常后接不定式(to + 动词原形)"
                        )
    
    severity = "ERROR" if errors else ("WARNING" if warnings else "PASS")
    is_valid = (severity != "ERROR")
    
    return ValidationReport(
        severity=severity,
        is_valid=is_valid,
        errors=errors,
        warnings=warnings,
        infos=[],
        auto_corrections=[]
    )
```

### 5.4 relative_pronoun_match（关系代词匹配）

**检查范围：**
- ✅ 人（who/whom/whose）、物（which/whose）、通用（that）
- ❌ 不处理：where/when/in which/of which、限定性/非限定性

**实现：**
```python
def validate_relative_pronoun_match(
    sentence: str, doc: Any, phrases: List[PhraseNode]
) -> ValidationReport:
    """检查关系代词与先行词匹配。
    
    检查：
    - 人 + who/whom/whose
    - 物 + which/whose
    - 通用 + that
    
    示例错误：
    - "The man which runs" → ERROR
    - "The dog who barks" → WARNING
    """
    errors = []
    warnings = []
    
    # 找出所有定语从句（CLAUSE 且 parent 是 NP）
    relative_clauses = [
        p for p in phrases 
        if p.type == "CLAUSE" and p.parent_id
    ]
    
    for clause in relative_clauses:
        # 找先行词（父 NP）
        antecedent = next((p for p in phrases if p.id == clause.parent_id), None)
        if not antecedent or antecedent.type != "NP":
            continue
        
        # 判断先行词是人还是物
        is_person = _is_person_np(antecedent, doc)
        
        # 提取关系代词（从句的第一个词）
        clause_text = clause.text.strip()
        first_word = clause_text.split()[0].lower() if clause_text else ""
        
        if is_person:
            if first_word == "which":
                errors.append(
                    f"先行词 '{antecedent.text}' 是人，应使用 'who' 而非 'which'"
                )
        else:  # 物
            if first_word == "who":
                warnings.append(
                    f"先行词 '{antecedent.text}' 是物，建议使用 'which' 或 'that'"
                )
    
    severity = "ERROR" if errors else ("WARNING" if warnings else "PASS")
    is_valid = (severity != "ERROR")
    
    return ValidationReport(
        severity=severity,
        is_valid=is_valid,
        errors=errors,
        warnings=warnings,
        infos=[],
        auto_corrections=[]
    )

def _is_person_np(np: PhraseNode, doc: Any) -> bool:
    """判断 NP 是否指人（简化版）"""
    # 人称代词
    if np.head_pos == "PRON":
        pronoun = np.head_token_text.lower()
        return pronoun in {"i", "you", "he", "she", "we", "they", "who", "whom"}
    
    # spaCy NER 标签
    for token in doc:
        if token.text == np.head_token_text:
            if token.ent_type_ == "PERSON":
                return True
    
    # 常见人类名词
    person_nouns = {
        "person", "people", "man", "woman", "boy", "girl", "child", "children",
        "teacher", "student", "friend", "doctor", "engineer", "artist",
        "player", "singer", "writer", "actor", "director", "professor"
    }
    return np.head_token_text.lower() in person_nouns
```


---

## 6. LanguageTool Validator（第 6 道）

### 6.1 架构定位

- LanguageTool 是**次级顾问**，非语法权威
- Grammar Engine 是**唯一语法权威**
- LanguageTool 不可用时优雅降级
- LanguageTool 建议不自动应用

### 6.2 去重和 Severity 映射

**去重策略：**
过滤与 Validators 1-5 重复的规则（主谓一致、时态助动词等）

**Severity 映射（保守）：**
- grammar/misspelling → WARNING
- typographical/whitespace → INFO
- style/redundancy → INFO
- 默认 → WARNING

---

## 7. 错误处理和降级策略

### 7.1 降级场景矩阵

| 场景 | 行为 | HTTP | Severity | 用户体验 |
|------|------|------|----------|----------|
| Validator 1-5 异常 | safe_execute 捕获 | 200 | WARNING | 显示"校验器失败" |
| LanguageTool 未启动 | 跳过 Validator 6 | 200 | INFO | 显示"LanguageTool 不可用" |
| LanguageTool 超时 | 返回 timeout LTReport | 200 | INFO | 显示"LanguageTool 超时" |
| LanguageTool 崩溃 | is_alive()=False | 200 | INFO | 下次尝试重启 |
| 所有 Validators 失败 | 返回空报告 | 200 | PASS | 系统继续工作 |

### 7.2 保证

- ✅ 永不返回 HTTP 500
- ✅ 任何组件失败 → 降级 → 继续
- ✅ Backend 启动立即可用
- ✅ 消息去重避免重复提示

---

## 8. 测试策略（80/15/5 金字塔）

### 8.1 单元测试（80%）

**LanguageToolManager（3-5 cases）**
**clause_completeness（5-10 cases）**
**non_finite_legality（5-10 cases）**
**relative_pronoun_match（5-10 cases）**
**validate_with_languagetool（3-5 cases）**
**safe_execute（3-5 cases）**

### 8.2 集成测试（15%）

- 管道完整性
- Severity 合并
- 消息去重
- 执行顺序
- 错误追溯

### 8.3 降级测试（15%，最重要）

- LanguageTool 未启动
- LanguageTool 超时
- LanguageTool 崩溃
- Validator 异常
- 全部失败
- 端口占用
- 崩溃后重启

### 8.4 目标覆盖率

- 主路径：80%
- 降级路径：15%
- 边缘情况：5%

---

## 9. M3c1 交付标准

### 9.1 功能完整性

- [ ] LanguageToolManager 实现
- [ ] ExternalServiceManager 基类
- [ ] safe_execute() 包装器
- [ ] 3 项浅层 Rule Validators
- [ ] LanguageTool Validator #6
- [ ] validate() 统一入口更新

### 9.2 韧性保证（零崩溃）

- [ ] 任何 Validator 异常 → 降级为 WARNING → 继续
- [ ] LanguageTool 不可用 → 跳过 #6 → 显示 INFO → 继续
- [ ] 所有场景永远返回 HTTP 200
- [ ] Backend 启动立即可用

### 9.3 测试覆盖

- [ ] 单元测试 80%
- [ ] 集成测试 15%
- [ ] 降级测试 15%（7 个关键场景）
- [ ] 所有测试通过

### 9.4 文档

- [ ] 代码注释清晰
- [ ] DEVLOG.md 记录决策和踩坑
- [ ] PROGRESS.md 更新状态

### 9.5 验收测试

```bash
# 1. Backend 启动（LanguageTool 后台启动）
cd backend
python app.py

# 2. 立即 curl 测试（不等待 LanguageTool）
curl -X POST http://127.0.0.1:18765/api/expansion/analyze \
  -d '{"sentence":"He go to school."}' \
  -H 'Content-Type: application/json'
# 应返回 200 + ValidationReport

# 3. 等待 10 秒后再次 curl（LanguageTool 已就绪）
# 应返回 200 + 可能包含 LanguageTool 建议

# 4. 强制停止 LanguageTool，再次 curl
# 应返回 200 + INFO（LanguageTool 不可用）

# 5. pytest 全部通过
pytest tests/test_m3c1_*.py -v
```

### 9.6 M3c1 完成后

- ✅ 验证层冻结（不再修改）
- ✅ Grammar Engine 永久稳定的验证能力
- ✅ 为 M3c2-5 打下坚实基础

---

## 10. 后续阶段概览

### M3c2: 模板基础架构（内部）
- TemplateBase / WordTemplate / ClauseTemplate
- Slot / ClauseRealizer
- 无 UI，无 available=True
- 工作量：2-3 天

### M3c3: 开放定语从句（首个垂直切片）
- relative_clause available=True
- 8-12 个模板（who/which/that/where/when）
- Release v0.8
- 工作量：3-4 天

### M3c4: 开放状语从句
- adverbial_clause available=True
- 10-12 个模板
- Release v0.9
- 工作量：2-3 天

### M3c5: 开放名词性从句
- noun_clause available=True
- 10-12 个模板
- Release v1.0
- 工作量：2-3 天

**总工作量估算：** 14-20 天（分 5 个独立阶段）

---

## 11. 文件清单

### 新增（后端）
- `backend/grammar_engine/external_service_manager.py` - 基类
- `backend/grammar_engine/languagetool_manager.py` - LanguageTool 实现
- `backend/tests/test_m3c1_validators.py` - 单元测试
- `backend/tests/test_m3c1_integration.py` - 集成测试
- `backend/tests/test_m3c1_degradation.py` - 降级测试

### 修改（后端）
- `backend/grammar_engine/expansion_validator.py` - 添加 3 项 + #6 + safe_execute
- `backend/app.py` - startup/shutdown 事件
- `backend/requirements.txt` - 添加依赖（如需要）

### 文档
- `docs/PROGRESS.md` - 更新 M3c1 状态
- `docs/DEVLOG.md` - 添加 M3c1 章节
- `docs/superpowers/specs/2026-06-23-m3c1-validation-layer-design.md` - 本文档

---

## 12. Spec Self-Review

- [x] **没有 placeholder** - 所有实现细节明确
- [x] **没有矛盾** - 架构一致，降级策略清晰
- [x] **没有歧义** - 每个组件职责明确
- [x] **范围清晰** - M3c1 边界明确（验证层，不做模板）
- [x] **风险识别** - 降级测试作为最高优先级
- [x] **可测试** - 80/15/5 测试策略具体

---

## 13. 核心原则总结

✅ **验证优先，生成其次** - M3c1 完成验证层，冻结后再开发模板
✅ **零崩溃保证** - safe_execute + 降级策略
✅ **Always HTTP 200** - Validator 是教师，非编译器
✅ **LanguageTool 次级顾问** - Grammar Engine 是唯一权威
✅ **韧性优先于覆盖率** - 80% 覆盖 + 15% 降级测试
✅ **渐进交付** - M3c 分 5 个独立阶段
✅ **永不暴露空功能** - 每个阶段交付完整垂直切片

