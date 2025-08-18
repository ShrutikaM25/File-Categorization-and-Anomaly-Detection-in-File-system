import React, { useState } from "react";
import { Routes, Route } from "react-router-dom";
import Home from "./components/Home/Home";
import FileClassifier from "./components/FileClassifier/FileClassifier";
import AnomalyDetector from "./components/AnomalyDetector";
import Navbar from "./components/Sidebar/Navbar";
import Sidebar from "./components/Sidebar/Sidebar";
import Dashboard from "./components/Dashboard/Dashboard";
import ExecutePipeline from "./components/ExecutePipeline/ExecutePipeline";

function App() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  return (
    <div className="flex flex-col h-screen">
      {/* Navbar */}
      <Navbar toggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)} />

      <div className="flex flex-1">
        {/* Sidebar */}
        <Sidebar isOpen={isSidebarOpen} />

        {/* Main Content */}
        <div className="flex-1 p-4 md:ml-64 mt-16 transition-all duration-300 bg-gray-200  ">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/classify" element={<FileClassifier />} />
            <Route path="/anomaly" element={<AnomalyDetector />} />
            <Route path="/anomaly/run-pipeline" element={<ExecutePipeline />} />
          </Routes>
        </div>
      </div>
    </div>
  );
}

export default App;
