"use client"

import { useState, useEffect } from "react"
import { useNavigate } from "react-router-dom"
import { motion, AnimatePresence } from "framer-motion"
import { FaPlay, FaSync, FaCheckCircle, FaChartBar, FaExclamationTriangle } from "react-icons/fa"
import Confetti from "react-confetti"

const ExecutePipeline = () => {
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)
  const [progress, setProgress] = useState(0)
  const [messageIndex, setMessageIndex] = useState(0)
  const navigate = useNavigate()

  const messages = [
    "🚀 Crunching data, hang tight...",
    "🔍 Detecting anomalies...",
    "🤖 AI is working its magic...",
    "📊 Generating insights...",
    "⏳ Almost there...",
  ]

  useEffect(() => {
    if (loading) {
      const progressInterval = setInterval(() => {
        setProgress((prev) => (prev < 100 ? prev + 2 : 100))
      }, 1500)

      const messageInterval = setInterval(() => {
        setMessageIndex((prev) => (prev + 1) % messages.length)
      }, 10000)

      return () => {
        clearInterval(progressInterval)
        clearInterval(messageInterval)
      }
    }
  }, [loading])

  const handleClick = async () => {
    setLoading(true)
    setSuccess(false)
    setProgress(0)

    try {
      const response = await fetch("http://localhost:5000/run-pipeline", {
        method: "POST",
      })
      const data = await response.json()
      console.log(data)
      setSuccess(true)
    } catch (error) {
      console.error("Error running pipeline:", error)
    }

    setLoading(false)
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-purple-50 to-white p-6 flex flex-col items-center justify-center">
      {/* Confetti effect when pipeline is done */}
      {success && <Confetti numberOfPieces={200} recycle={false} />}

      <div className="max-w-3xl w-full flex flex-col items-center">
    
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className={`px-8 py-4 text-lg font-semibold rounded-xl transition-all duration-300 shadow-md flex items-center gap-3 ${
            loading ? "bg-gray-400 cursor-not-allowed" : "bg-purple-600 text-white hover:bg-purple-700"
          }`}
          onClick={handleClick}
          disabled={loading}
        >
          {loading ? (
            <>
              <FaSync className="animate-spin h-5 w-5" />
              <span>Processing...</span>
            </>
          ) : (
            <>
              <FaPlay className="h-5 w-5" />
              <span>Start Pipeline</span>
            </>
          )}
        </motion.button>

        {/* Progress Bar */}
        {loading && (
          <div className="mt-8 w-full max-w-md">
            <div className="flex justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">Progress</span>
              <span className="text-sm font-medium text-purple-600">{progress}%</span>
            </div>
            <div className="h-4 bg-gray-200 rounded-full overflow-hidden shadow-inner">
              <motion.div
                className="h-full bg-gradient-to-r from-purple-600 to-orange-500 rounded-full"
                initial={{ width: "0%" }}
                animate={{ width: `${progress}%` }}
                transition={{ duration: 1, ease: "linear" }}
              />
            </div>
          </div>
        )}

        {/* Dynamic Motivational Messages */}
        <AnimatePresence mode="wait">
          {loading && (
            <motion.div
              key={messageIndex}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.5 }}
              className="mt-6 p-4 bg-purple-50 rounded-lg border border-purple-100 text-center"
            >
              <p className="text-lg text-purple-800 font-medium">{messages[messageIndex]}</p>
              <div className="flex justify-center mt-3 space-x-1">
                <div
                  className="w-2 h-2 bg-purple-600 rounded-full animate-bounce"
                  style={{ animationDelay: "0ms" }}
                ></div>
                <div
                  className="w-2 h-2 bg-purple-600 rounded-full animate-bounce"
                  style={{ animationDelay: "300ms" }}
                ></div>
                <div
                  className="w-2 h-2 bg-purple-600 rounded-full animate-bounce"
                  style={{ animationDelay: "600ms" }}
                ></div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Success Message & Buttons */}
        <AnimatePresence>
          {success && (
            <motion.div
              key="success"
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.5 }}
              transition={{ duration: 0.5 }}
              className="flex flex-col items-center mt-8 w-full"
            >
              <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mb-4">
                <FaCheckCircle className="w-12 h-12 text-green-500" />
              </div>
              <h2 className="text-2xl font-bold text-gray-800 mb-2">Pipeline Completed! 🎉</h2>
              <p className="text-gray-600 text-center mb-8">
                The anomaly detection process has finished successfully. You can now view the results.
              </p>

              {/* Buttons to navigate after success */}
              <div className="flex flex-wrap gap-4 justify-center">
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  className="px-6 py-3 text-base font-medium rounded-xl bg-purple-600 text-white hover:bg-purple-700 transition shadow-md flex items-center gap-2"
                  onClick={() => navigate("/dashboard")}
                >
                  <FaChartBar className="h-5 w-5" />
                  <span>View Analytical Dashboard</span>
                </motion.button>

                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  className="px-6 py-3 text-base font-medium rounded-xl bg-orange-500 text-white hover:bg-orange-600 transition shadow-md flex items-center gap-2"
                  onClick={() => navigate("/anomaly")}
                >
                  <FaExclamationTriangle className="h-5 w-5" />
                  <span>View Anomalies With Reasons</span>
                </motion.button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}

export default ExecutePipeline

