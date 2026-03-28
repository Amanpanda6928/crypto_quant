import { createChart } from "lightweight-charts";
import { useEffect, useRef } from "react";

export default function CandleChart({ data }) {
  const ref = useRef();

  useEffect(() => {
    const chart = createChart(ref.current, { width:800, height:300 });
    const candle = chart.addCandlestickSeries();

    const d = Object.values(data).map((x,i)=>({
      time:i,
      open:x.price*0.99,
      high:x.price*1.01,
      low:x.price*0.98,
      close:x.price
    }));

    candle.setData(d);

  }, [data]);

  return <div ref={ref}></div>;
}
