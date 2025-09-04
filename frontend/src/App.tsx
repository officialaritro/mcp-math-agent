import React from "react";
import Chat from "./components/Chat";

function App() {
  return (
    <div className="min-h-screen bg-gray-100 p-6">
      <div className="max-w-3xl mx-auto bg-white rounded-lg shadow p-6">
        <h1 className="text-2xl font-bold mb-4">AgentTuring — Math Tutor</h1>
        <Chat />
      </div>
    </div>
  );
}

export default App;
