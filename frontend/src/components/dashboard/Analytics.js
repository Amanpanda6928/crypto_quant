import { useEffect, useState } from "react";
import { api } from "../../api/http";

export default function Analytics() {
  const [d,setD]=useState({});

  useEffect(()=>{
    api.get("/analytics").then(r=>setD(r.data));
  },[]);

  return (
    <div>
      Sharpe: {d.sharpe} | Profit: {d.profit}
    </div>
  );
}
