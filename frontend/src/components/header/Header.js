export default function Header({ data }) {
  const coins = Object.values(data);
  const avg = coins.length
    ? coins.reduce((a,b)=>a+b.confidence,0)/coins.length
    : 0;

  return (
    <div className="header">

      <span className="live">● LIVE</span>

      <span className="signal">
        {coins[0]?.signal || "HOLD"}
      </span>

      <span className="trend">
        ▲ {coins[0]?.prediction?.toFixed(2)}
      </span>

      <div className="bar">
        <div style={{width:`${avg}%`}}></div>
      </div>

      <span>{avg.toFixed(1)}%</span>

    </div>
  );
}
