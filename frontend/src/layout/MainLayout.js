export default function MainLayout({ data }) {
  return (
    <div className="main-layout">
      <div className="content">
        {Object.keys(data).map(coin => (
          <div key={coin} className="coin-card">
            <h3>{coin}</h3>
            <p>Price: ${data[coin]?.price?.toFixed(2)}</p>
            <p>Signal: {data[coin]?.signal}</p>
            <p>Confidence: {data[coin]?.confidence}%</p>
          </div>
        ))}
      </div>
    </div>
  );
}
