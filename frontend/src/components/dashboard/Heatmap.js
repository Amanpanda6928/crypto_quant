export default function Heatmap({ data }) {
  const coins = Object.keys(data);
  
  return (
    <div className="heatmap">
      {coins.map(coin => {
        const signal = data[coin]?.signal;
        const color = signal === "BUY" ? "#00ff00" : signal === "SELL" ? "#ff0000" : "#666666";
        
        return (
          <div key={coin} style={{ backgroundColor: color, padding: "10px", margin: "2px" }}>
            {coin}
          </div>
        );
      })}
    </div>
  );
}
