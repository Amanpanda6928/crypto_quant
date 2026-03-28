import { useEffect, useState } from "react";
import { api } from "../../api/http";

export default function History() {
  const [t,setT]=useState([]);

  useEffect(()=>{
    api.get("/history/1").then(r=>setT(r.data));
  },[]);

  return (
    <div>
      {t.map((x,i)=><div key={i}>{x.symbol} {x.action}</div>)}
    </div>
  );
}
