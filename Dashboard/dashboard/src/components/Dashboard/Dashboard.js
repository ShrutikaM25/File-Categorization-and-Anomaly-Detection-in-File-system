"use client"

import { useState, useEffect } from "react"
import { FaExclamationTriangle } from "react-icons/fa"
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Legend,
  LineChart,
  Line,
} from "recharts"
import HeatMap from "react-heatmap-grid"

// Category Bar Chart Component
const CategoryBarChart = ({ bardata }) => {
  // Convert the category-wise distribution object into an array
  const data = Object.keys(bardata).map((category) => ({
    category,
    count: bardata[category],
  }))

  return (
    <BarChart width={800} height={300} data={data}>
      <CartesianGrid strokeDasharray="3 3" />
      <XAxis dataKey="category" interval={0} tick={{ angle: -45, textAnchor: "end" }} height={60} />
      <YAxis />
      <Tooltip />
      <Legend />
      <Bar dataKey="count" fill="#7e22ce" /> {/* Updated to purple-700 */}
    </BarChart>
  )
}

// Operation vs. Category Heat Map Component
const OperationCategoryHeatMap = ({ data }) => {
  const [heatmapData, setHeatmapData] = useState([])
  const [operations, setOperations] = useState([])
  const [categories, setCategories] = useState([])

  useEffect(() => {
    if (data && Array.isArray(data)) {
      setHeatmapData(data)
      // Extract unique operations and categories
      const ops = [...new Set(data.map((item) => item.operation))]
      const cats = [...new Set(data.map((item) => item.category))]
      setOperations(ops)
      setCategories(cats)
    }
  }, [data])

  // Build grid: each cell corresponds to the count for the (operation, category) pair.
  const gridData = operations.map((op) =>
    categories.map((cat) => {
      const found = heatmapData.find((item) => item.operation === op && item.category === cat)
      return found ? found.count : 0
    }),
  )

  return (
    <div className="p-4">
      {/* <h2 className="text-xl font-bold mb-4">Operation vs. Category Heat Map</h2> */}
      <HeatMap
        xLabels={categories}
        yLabels={operations}
        data={gridData}
        cellStyle={(background, value, min, max) => ({
          background: `rgba(126, 34, 206, ${max > 0 ? value / max : 0})`, // Updated to purple-700
          fontSize: "11px",
          color: value > max / 2 ? "#fff" : "#000",
        })}
        cellRender={(value) => value && <span>{value}</span>}
      />
    </div>
  )
}

const AnomalyTrendChart = ({ data }) => {
  const [trendData, setTrendData] = useState([])

  useEffect(() => {
    if (data) {
      setTrendData(data)
    }
  }, [data])

  return (
    <>
      <LineChart width={800} height={300} data={trendData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" />
        <YAxis />
        <Tooltip />
        <Legend />
        <Line type="monotone" dataKey="count" stroke="#7e22ce" name="Daily Count" /> {/* Updated to purple-700 */}
        <Line type="monotone" dataKey="movingAverage" stroke="#f97316" name="7-day Moving Avg" />{" "}
        {/* Updated to orange-500 */}
      </LineChart>
    </>
  )
}

// Dashboard Component
const Dashboard = () => {
  const [totalAnomalies, setTotalAnomalies] = useState(0)
  const [anomalyCounts, setAnomalyCounts] = useState({})
  const [anomaliesOverTime, setAnomaliesOverTime] = useState([])
  const [operationCategoryHeatMapData, setOperationCategoryHeatMapData] = useState([])
  const [anomalyTrend, setanomalyTrend] = useState({})
  const [operationWiseDistribution, setOperationWiseDistribution] = useState({})
  const [categoryWiseDistribution, setCategoryWiseDistribution] = useState({})
  const [loading, setLoading] = useState(true)
  const [selectedInterval, setSelectedInterval] = useState("weekly")

  useEffect(() => {
    const fetchAnomalyData = async () => {
      try {
        const [countRes, timeRes, categoryRes, opCatRes, trendRes] = await Promise.all([
          fetch("http://127.0.0.1:5000/get-anomaly-counts"),
          fetch("http://127.0.0.1:5000/get-anomalies-over-time"),
          fetch("http://127.0.0.1:5000/get-category-anomaly-count"),
          fetch("http://127.0.0.1:5000/get-operation-category-heatmap"),
          fetch("http://127.0.0.1:5000/get-anomaly-trend"),
        ])

        const countData = await countRes.json()
        const timeData = await timeRes.json()
        const categoryData = await categoryRes.json()
        const opCatData = await opCatRes.json()
        const trenddata = await trendRes.json()

        setTotalAnomalies(countData.total_anomalies || 0)
        setAnomalyCounts(countData.operation_counts || {})
        setAnomaliesOverTime(
          Object.entries(timeData.anomalies_over_time || {}).map(([date, count]) => ({
            date,
            count,
          })),
        )
        setOperationWiseDistribution(countData.operation_counts || {})
        setCategoryWiseDistribution(categoryData.category_anomaly_count || {})
        setOperationCategoryHeatMapData(opCatData.heatmap || [])
        setanomalyTrend(trenddata.trend)
      } catch (error) {
        console.error("Error fetching anomaly data:", error)
      } finally {
        setLoading(false)
      }
    }

    fetchAnomalyData()
  }, [selectedInterval])

  // Convert anomaly counts into chart data for the Pie chart
  const pieChartData = Object.entries(anomalyCounts).map(([operation, count]) => ({
    name: operation,
    value: count,
  }))

  // Colors for Pie Chart - Updated to match homepage
  const COLORS = ["#7e22ce", "#9333ea", "#a855f7", "#f97316", "#fb923c"]

  return (
    <div className="min-h-screen p-6 text-gray-900 bg-gradient-to-b from-purple-50 to-white">
      <div className="mb-6 px-4">
        <h1 className="text-2xl font-bold text-gray-800">Anomaly Dashboard</h1>
        <p className="text-gray-600">Overview of anomalies detected over time and by Operation.</p>
      </div>

      {loading ? (
        <p className="text-center text-lg font-semibold text-gray-500">Loading data...</p>
      ) : (
        <>
          {/* Total Anomalies & Operations Count Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="p-6 bg-white rounded-lg shadow-md border border-gray-200 flex justify-between items-center">
              <div>
                <h2 className="text-xl font-semibold text-black">Total Anomalies</h2>
                <p className="text-3xl font-bold text-purple-700">{totalAnomalies}</p>
              </div>
              <FaExclamationTriangle className="text-purple-700 text-4xl" />
            </div>

            {pieChartData.map((data, index) => (
              <div
                key={data.name}
                className="p-6 bg-white rounded-lg shadow-md border border-gray-200 flex justify-between items-center"
              >
                <div>
                  <h2 className="text-xl font-semibold capitalize">{data.name}</h2>
                  <p className="text-3xl font-bold text-orange-500">{data.value}</p>
                </div>
                <FaExclamationTriangle className="text-orange-500 text-4xl" />
              </div>
            ))}
          </div>

          {/* Charts Section */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-8">
            {/* Anomalies Over Time (Line Chart) */}
            <div className="bg-white p-6 rounded-lg shadow-md col-span-1 md:col-span-2">
              <h2 className="text-xl font-semibold mb-4 text-gray-800">Anomalies Over Time</h2>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={anomaliesOverTime}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="count" stroke="#7e22ce" /> {/* Updated to purple-700 */}
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Anomalies by Operation Type (Pie Chart) */}
            <div className="bg-white p-6 rounded-lg shadow-md col-span-1 md:col-span-2">
              <h2 className="text-xl font-semibold mb-4 text-gray-800">Anomaly Distribution by Operation</h2>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={pieChartData}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={100}
                    fill="#7e22ce"
                    label={({ name, value }) => `${name}: ${value}`}
                  >
                    {pieChartData.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>

            {/* Operation-Wise Anomaly Distribution (Bar Chart) */}
            <div className="bg-white p-6 rounded-lg shadow-md col-span-1 md:col-span-2">
              <h2 className="text-xl font-semibold mb-4 text-gray-800">Operation-Wise Anomaly Distribution</h2>
              <ResponsiveContainer width="100%" height={300}>
                <CategoryBarChart bardata={operationWiseDistribution} />
              </ResponsiveContainer>
            </div>

            {/* Category-Wise Anomaly Distribution (Bar Chart) */}
            <div className="bg-white p-6 rounded-lg shadow-md col-span-1 md:col-span-2">
              <h2 className="text-xl font-semibold mb-4 text-gray-800">Category-Wise Anomaly Distribution</h2>
              <ResponsiveContainer width="100%" height={300}>
                <CategoryBarChart bardata={categoryWiseDistribution} />
              </ResponsiveContainer>
            </div>

            {/* Heat Map Component */}
            <div className="bg-white p-6 rounded-lg shadow-md col-span-1 md:col-span-2">
              <h2 className="text-xl font-semibold mb-4 text-gray-800">
                Relationship between Operation Types and Categories (Operation vs. Category Heat Map)
              </h2>
              <ResponsiveContainer width="100%" height={300}>
                <OperationCategoryHeatMap data={operationCategoryHeatMapData} />
              </ResponsiveContainer>
            </div>

            {/* Trend Analysis */}
            <div className="bg-white p-6 rounded-lg shadow-md col-span-1 md:col-span-2">
              <h2 className="text-xl font-semibold mb-4 text-gray-800">Anomaly Trend Analysis</h2>
              <ResponsiveContainer width="100%" height={300}>
                <AnomalyTrendChart data={anomalyTrend} />
              </ResponsiveContainer>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

export default Dashboard

