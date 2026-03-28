export default function MarketTable({ data }) {
  const coins = Object.entries(data);

  return (
    <div className="market-table">
      <table>
        <thead>
          <tr>
            <th>Symbol</th>
            <th>Price</th>
            <th>Signal</th>
            <th>Confidence</th>
          </tr>
        </thead>
        <tbody>
          {coins.map(([symbol, d]) => (
            <tr key={symbol}>
              <td>{symbol}</td>
              <td>${d.price?.toFixed(2)}</td>
              <td>{d.signal}</td>
              <td>{d.confidence}%</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
