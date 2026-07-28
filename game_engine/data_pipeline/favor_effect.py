def favor2source(favor: int) -> float:
      """好感度对 SOURCE 的全局乘数 (GET_REVISION 饱和曲线)"""
      if favor <= 0:
          return 1.0
      # 公式: cap - rate*cap/(rate+x),这里 cap=200, rate=20000
      return (200 - 20000 * 200 / (20000 + favor)) / 100 + 1.0