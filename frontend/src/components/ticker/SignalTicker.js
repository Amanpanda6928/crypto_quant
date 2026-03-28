export default function SignalTicker({ data }) {
  return (
    <div className="ticker">
      <div className="ticker-track">
        {Object.keys(data).map(c=>(
          <span key={c}>
            {c} {data[c].signal} {data[c].confidence}%
          </span>
        ))}
      </div>
    </div>
  );
}
