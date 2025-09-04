import React, { useState } from "react";

export default function Chat() {
  const [q, setQ] = useState("");
  const [answer, setAnswer] = useState<string | null>(null);
  const [route, setRoute] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit() {
    setLoading(true);
    setAnswer(null);
    try {
      const resp = await fetch("/ask", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({question: q})
      });
      if (!resp.ok) {
        const j = await resp.json();
        alert(j.detail || "Request failed");
        setLoading(false);
        return;
      }
      const data = await resp.json();
      setAnswer(data.answer);
      setRoute(data.route);
    } catch (e) {
      alert("Network error");
    } finally {
      setLoading(false);
    }
  }

  async function sendFeedback(rating: number) {
    await fetch("/feedback", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({question: q, answer, rating, route})
    });
    alert("Thanks for the feedback!");
  }

  return (
    <div>
      <textarea className="w-full p-2 border rounded" rows={4} value={q} onChange={e=>setQ(e.target.value)} />
      <div className="mt-2 flex gap-2">
        <button className="px-4 py-2 bg-blue-600 text-white rounded" onClick={submit} disabled={loading || !q}>
          {loading ? "Thinking..." : "Ask"}
        </button>
      </div>
      {answer && (
        <div className="mt-4 p-4 border rounded bg-gray-50">
          <div className="text-sm text-gray-500">via: {route}</div>
          <div className="mt-2 whitespace-pre-wrap">{answer}</div>
          <div className="mt-4">
            <button onClick={()=>sendFeedback(1)} className="mr-2 px-3 py-1 border rounded">Bad</button>
            <button onClick={()=>sendFeedback(5)} className="px-3 py-1 border rounded">Good</button>
          </div>
        </div>
      )}
    </div>
  );
}
