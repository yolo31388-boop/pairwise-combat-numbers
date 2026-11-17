# pairwise-combat-numbers

数值策划抽查发现同等级同装备的伤害差了 3 倍，暴击率 50% 却每一下都暴击，抗性堆到 150% 反而开始回血，坦克血量被打成负数还继续算仇恨，连击加成叠到第 10 层直接秒杀。查下来是 game/combat.py 的伤害结算有严重问题：mitigate() 用固定减伤，护甲越高越接近无敌，护甲为 0 时又是另一套结果；crit_damage() 完全不看 roll，每次都按暴击算；resist_damage() 不做上下限裁剪，抗性超过 100% 变成治疗；glancing_factor() 恒为 1，等级差没有意义；dodge_chance() 用固定分母，等级越高闪避越离谱；block_damage() 不看是否格挡成功，所有伤害都减盾值；dot_ticks() 把总伤害按持续时长平均，每跳伤害算错；variance_damage() 忽略 roll，伤害没有任何浮动；combine_modifiers() 先乘百分比再减固定值，结算顺序反了；apply_hp_damage() 允许负血量；heal_amount() 不做治疗削减；combo_multiplier() 不设上限，层数越高越离谱；effective_armor() 忽略穿透；is_executable() 永远返回可斩杀。你要修的是：减伤按护甲曲线并处理零护甲；暴击按 roll 判定；抗性裁剪到 0-90%；等级差影响偏斜；闪避按等级递减；格挡只在成功时减伤；DoT 按跳数均分；伤害浮动按 roll；固定值先于百分比；血量下限为 0；治疗按削减比例；连击加成封顶；护甲先减固定再乘穿透百分比；斩杀线含等号。game/combat.py 是核心，tests/test_combat.py 15个红。

## 运行

```
python -m pytest tests -q
```

初始状态：15 个用例失败。修复实现使全部用例通过，不要修改 `tests/` 下的测试。
