import Header from "../header/Header";
import SignalTicker from "../ticker/SignalTicker";
import MarketTable from "./MarketTable";
import CandleChart from "./CandleChart";
import Heatmap from "./Heatmap";
import Analytics from "./Analytics";
import History from "./History";
import Backtest from "../Backtest";
import BacktestReal from "../BacktestReal";
import Portfolio from "../Portfolio";

export default function Dashboard({ data }) {
  return (
    <div>

      <Header data={data} />
      <SignalTicker data={data} />

      <CandleChart data={data} />
      <Heatmap data={data} />
      <MarketTable data={data} />
      <Analytics />
      <History />
      <Backtest />
      <BacktestReal />
      <Portfolio />

    </div>
  );
}
