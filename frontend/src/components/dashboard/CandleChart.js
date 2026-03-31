import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { useEffect, useState } from "react";

export default function CandleChart({ data }) {
  const [chartData, setChartData] = useState([]);

  useEffect(() => {
    if (data?.chartData) {
      const formatted = data.chartData.map((item, index) => ({
        name: item.time || `T${index}`,
        price: item.close || item.price,
        high: item.high,
        low: item.low,
        open: item.open
      }));
      setChartData(formatted);
    }
  }, [data]);

  return (
    <div style={{ width: '100%', height: 300, backgroundColor: '#0b0f14', padding: '20px' }}>
      <h3 style={{ color: '#ffffff', marginBottom: '20px' }}>Price Chart</h3>
      <ResponsiveContainer width="100%" height={250}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#333" />
          <XAxis dataKey="name" stroke="#fff" />
          <YAxis stroke="#fff" />
          <Tooltip 
            contentStyle={{ backgroundColor: '#111', border: '1px solid #333' }}
            labelStyle={{ color: '#fff' }}
          />
          <Line 
            type="monotone" 
            dataKey="price" 
            stroke="#00ff99" 
            strokeWidth={2}
            dot={{ fill: '#00ff99', r: 4 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
