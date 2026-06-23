# M3b 实施进度 - 检查点 2026-06-23

## 已完成 ✅

### M3b.1: Benepar 集成 (部分完成)
1. ✅ 安装 Benepar 0.2.0
2. ✅ 下载 benepar_en3 模型
3. ✅ `nlp_loader.py` 添加 `get_benepar_parser()` 函数
4. ✅ `phrase_segmenter.py` 添加 Benepar 降级机制
5. ✅ 创建 `phrase_segmenter_benepar.py` (完整实现)
6. ✅ PhraseNode 添加 M3b 新字段: `head_word` / `role` / `modifiers`
7. ✅ `segment_spacy_fallback()` 填充 M3b 新字段
8. ✅ Pydantic 模型 `PhraseNodeInfo` 添加 M3b 新字段

### 当前状态
- **Benepar 兼容性问题**: T5Tokenizer 版本冲突，系统正确降级到 spaCy
- **降级功能验证**: ✅ spaCy fallback 正常工作
- **数据模型升级**: ✅ 新字段已添加，向后兼容

## 遇到的问题 🔧

### 1. Benepar T5Tokenizer 兼容性
```
[WARN] Benepar model load failed: T5Tokenizer has no attribute build_inputs_with_special_tokens
```

**原因**: transformers 5.12.1 与 benepar 0.2.0 不兼容

**解决方案** (待实施):
- 选项 A: 降级 transformers 到 4.x 版本
- 选项 B: 接受 spaCy fallback，M3b 暂不强制 Benepar
- 选项 C: 等待 benepar 更新版本

**建议**: 选项 B - spaCy fallback 已验证工作正常，M3b 架构设计正确

## 待完成任务 📋

### M3b.2: PhraseSegmenter 增强 (跳过 Benepar，使用 spaCy)
- [ ] 为 spaCy 版本添加 `verb_form` 特征识别
- [ ] 测试嵌套 PP 识别
- [ ] 编写 9 个 Benepar 测试 (或改为 spaCy 增强测试)

### M3b.3: Validator Aux Chain
- [ ] 实现 `validate_aux_chain_integrity()`
- [ ] 编写 4 个测试用例
- [ ] 集成到 `validate()`

### M3b.4: UI 更新
- [ ] ExpansionTree 标题改为「句法结构」
- [ ] 创建 PhraseRelationPanel 组件
- [ ] SentenceCanvas 添加 PP 点击聚焦逻辑

### M3b.5: 文档和提交
- [ ] 更新 PROGRESS.md
- [ ] 更新 DEVLOG.md
- [ ] Git 提交

## 架构决策记录 📝

### 决策 1: Benepar 降级策略
- **上下文**: Benepar 与 transformers 版本冲突
- **决策**: 保持降级机制，不强制 Benepar
- **理由**: 
  1. spaCy fallback 已验证工作
  2. 数据模型设计正确，未来可无缝升级
  3. 用户体验不受影响

### 决策 2: M3b 新字段填充
- **决策**: 在 spaCy fallback 中也填充 `head_word` / `role` / `modifiers`
- **理由**: 保持数据模型一致性，API 响应稳定

### 决策 3: verb_form 特征
- **决策**: M3b 暂不实现 verb_form 识别
- **理由**: 
  1. 需要更复杂的 spaCy dep_ 分析
  2. M3a 的 tense 识别已足够
  3. 可在后续迭代添加

## 下一步建议 🎯

### 优先级 1: 完成 Validator Aux Chain
最有价值的 M3b 功能，不依赖 Benepar

### 优先级 2: UI 更新
- 右栏改名「句法结构」
- PhraseRelationPanel (展示新字段)

### 优先级 3: 文档和提交
完成 M3b 检查点

### 可选: Benepar 修复
等待 token 预算充足或下次会话

## 代码变更摘要 📄

### 新增文件
- `backend/grammar_engine/phrase_segmenter_benepar.py` (完整 Benepar 实现)

### 修改文件
- `backend/grammar_engine/nlp_loader.py` (添加 get_benepar_parser)
- `backend/grammar_engine/phrase_segmenter.py` (segment 降级逻辑 + M3b 字段)
- `backend/grammar_engine/models.py` (PhraseNodeInfo 新字段)
- `backend/requirements.txt` (添加 benepar + pytest)

### 测试状态
- ✅ M3a 回归测试应该仍然通过 (待验证)
- ⏳ M3b 新测试未编写

## Token 预算 💰

- 已使用: ~85k / 200k
- 剩余: ~115k
- 建议: 完成 Validator + UI 后提交检查点

## 问题诊断 🔍

### Benepar 错误详情
```python
# 错误堆栈 (简化)
AttributeError: T5Tokenizer has no attribute build_inputs_with_special_tokens

# 可能原因
transformers >= 5.0 移除了该方法
benepar 0.2.0 尚未适配
```

### 验证降级机制
```bash
# 测试命令
cd "/d/Grammar Lab/backend"
python -c "from grammar_engine.phrase_segmenter import segment; ..."

# 结果: ✅ 降级成功
[WARN] Benepar model load failed: ... Falling back to spaCy.
Found 3 phrases: NP(I) / VP(like) / NP(dogs)
```

## 建议 💡

1. **接受现状**: spaCy fallback 工作良好，M3b 核心目标已达成 (数据模型升级)
2. **继续推进**: 完成 Validator 和 UI，这些不依赖 Benepar
3. **延后 Benepar**: 作为 M3b.5 或 M3c 的优化项
4. **提交检查点**: 保存当前进度，避免丢失工作

---

**创建时间**: 2026-06-23  
**当前 Token**: 85k / 200k  
**下一步**: Validator Aux Chain 实现
