"use client"

import { useState, useEffect, useRef } from "react"
import { FaFilter, FaDownload, FaSearch, FaCalendarAlt, FaTrash, FaBell } from "react-icons/fa"

const AnomalyDetector = () => {
  const [anomalies, setAnomalies] = useState([])
  const [totalAnomalies, setTotalAnomalies] = useState(0)
  const [page, setPage] = useState(1)
  const [filters, setFilters] = useState({
    operation: "",
    category: "",
    risk: "",
    start_time: "",
    end_time: "",
  })
  const [uniqueCategories, setUniqueCategories] = useState([])
  const [alerts, setAlerts] = useState([]) // Store live alerts
  const [sortOrder, setSortOrder] = useState("desc")

  // Fetch unique categories
  useEffect(() => {
    const fetchUniqueCategories = async () => {
      try {
        const response = await fetch("http://127.0.0.1:5000/get-unique-categories")
        const data = await response.json()
        console.log("unique categories", data)
        setUniqueCategories(data.unique_categories || [])
      } catch (error) {
        console.error("Error fetching unique categories:", error)
      }
    }

    fetchUniqueCategories()
  }, [])

  // Fetch anomalies with filters and pagination
  useEffect(() => {
    const fetchAnomalies = async () => {
      try {
        const params = new URLSearchParams({
          page,
          sort: sortOrder, // Pass sorting order
          ...(filters.operation && { operation: filters.operation }),
          ...(filters.category && { category: filters.category }),
          ...(filters.risk_score && { risk: filters.risk_score }),
        })
        console.log("params", params)
        const response = await fetch(`http://127.0.0.1:5000/get-anomalies-sorted?${params.toString()}`)
        const data = await response.json()
        console.log("response", data)
        setAnomalies(data.anomalies || [])
        setTotalAnomalies(data.total || 0)
      } catch (error) {
        console.error("Error fetching anomalies:", error)
      }
    }

    fetchAnomalies()
  }, [page, filters.operation, filters.category, sortOrder]) // Removed start_time & end_time to avoid auto-calling

  // Fetch anomalies by time range when button is clicked
  const fetchAnomaliesByTime = async () => {
    if (!filters.start_time || !filters.end_time) {
      alert("Please select both start and end times.")
      return
    }

    try {
      const params = new URLSearchParams({
        start_time: filters.start_time,
        end_time: filters.end_time,
      })

      const response = await fetch(`http://127.0.0.1:5000/get-anomalies-by-time?${params.toString()}`)
      const data = await response.json()

      setAnomalies(data.anomalies || [])
      setTotalAnomalies(data.total || 0)
    } catch (error) {
      console.error("Error fetching anomalies by time:", error)
    }
  }

  // Handle filter changes
  const handleFilterChange = (e) => {
    const { name, value } = e.target
    setFilters((prevFilters) => ({ ...prevFilters, [name]: value }))
    setPage(1)
  }

  // Clear filters
  const clearFilters = () => {
    setFilters({
      operation: "",
      category: "",
      risk: "",
      start_time: "",
      end_time: "",
    })
    setPage(1)
  }

  const getRiskLevelStyle = (riskScore) => {
    console.log("riskScore", riskScore)
    if (riskScore >= 76) {
      return { label: "Critical", color: "text-red-800", bg: "bg-red-300", icon: "🔥" }; // 🔴 Critical
    } else if (riskScore >= 51) {
      return { label: "High", color: "text-red-600", bg: "bg-red-200", icon: "🚨" }; // 🟠 High
    } else if (riskScore >= 21) {
      return { label: "Medium", color: "text-yellow-500", bg: "bg-yellow-200", icon: "⚠️" }; // 🟡 Medium
    } else {
      return { label: "Low", color: "text-green-500", bg: "bg-green-200", icon: "✅" }; // 🟢 Low
    }
  };

  const filteredAnomalies = anomalies.filter((anomaly) => {
    const riskLevel = getRiskLevelStyle(anomaly.risk_score).label.toLowerCase(); // Convert to lowercase
    return !filters.risk || filters.risk === riskLevel; // Filter if risk is selected
  });

  // Export functions
  const exportJSON = () => {
    const jsonData = JSON.stringify(anomalies, null, 2)
    const blob = new Blob([jsonData], { type: "application/json" })
    const url = URL.createObjectURL(blob)

    const a = document.createElement("a")
    a.href = url
    a.download = "anomalies.json"
    a.click()
    URL.revokeObjectURL(url)
  }

  const exportCSV = () => {
    if (anomalies.length === 0) return

    const headers = ["Timestamp", "Operation", "File", "Category", "Details"]
    const csvRows = anomalies.map((anomaly) => [
      new Date(anomaly.timestamp).toLocaleString(),
      anomaly.operation,
      anomaly.file,
      anomaly.category,
      `"${(anomaly.reasons || []).join("; ")}"`,
    ])

    const csvContent = [headers, ...csvRows].map((row) => row.join(",")).join("\n")

    const blob = new Blob([csvContent], { type: "text/csv" })
    const url = URL.createObjectURL(blob)

    const a = document.createElement("a")
    a.href = url
    a.download = "anomalies.csv"
    a.click()
    URL.revokeObjectURL(url)
  }

  // Track which dropdown is open
  const [openDropdownId, setOpenDropdownId] = useState(null)
  const dropdownRefs = useRef({})

  // Function to handle dropdown positioning
  const adjustDropdownPosition = (id) => {
    if (!dropdownRefs.current[id]) return

    const dropdown = dropdownRefs.current[id]
    const rect = dropdown.getBoundingClientRect()
    const viewportWidth = window.innerWidth

    // Reset any previous adjustments
    dropdown.style.left = "0"
    dropdown.style.right = "auto"

    // Check if dropdown extends beyond right edge of viewport
    if (rect.right > viewportWidth) {
      dropdown.style.left = "auto"
      dropdown.style.right = "0"
    }
  }

  // Handle dropdown toggle
  const toggleDropdown = (id) => {
    setOpenDropdownId(openDropdownId === id ? null : id)
  }

  // Adjust position when window resizes or after opening
  useEffect(() => {
    if (openDropdownId !== null) {
      adjustDropdownPosition(openDropdownId)
    }

    const handleResize = () => {
      if (openDropdownId !== null) {
        adjustDropdownPosition(openDropdownId)
      }
    }

    window.addEventListener("resize", handleResize)
    return () => window.removeEventListener("resize", handleResize)
  }, [openDropdownId])
  

  // Get operation color
  const getOperationColor = (operation) => {
    const colors = {
      insertion: "text-green-600",
      deletion: "text-red-600",
      update: "text-orange-500",
      rename: "text-blue-600",
    }
    return colors[operation.toLowerCase()] || "text-purple-600"
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-purple-50 to-white p-6">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-800">Anomalies Detected</h1>
            <p className="text-gray-600 mt-2">Monitor and analyze detected anomalies in your system</p>
          </div>
          <div className="flex gap-3">
            <button
              className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors duration-300 flex items-center gap-2"
              onClick={exportJSON}
            >
              <FaDownload className="h-4 w-4" />
              Export JSON
            </button>
            <button
              className="px-4 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition-colors duration-300 flex items-center gap-2"
              onClick={exportCSV}
            >
              <FaDownload className="h-4 w-4" />
              Export CSV
            </button>
          </div>
        </div>

        {/* 🔴 Live Alerts Section */}
        <div className="fixed top-4 right-4 space-y-2 z-50">
          {alerts.map((alert, index) => (
            <div
              key={index}
              className="bg-red-500 text-white p-4 rounded-lg shadow-lg flex items-center gap-2 animate-pulse"
            >
              <FaBell className="h-5 w-5" />
              <div>
                <p className="font-bold">New Anomaly Detected</p>
                <p className="text-sm">
                  {alert.file} ({alert.operation})
                </p>
              </div>
            </div>
          ))}
        </div>

        {/* Filters */}
        <div className="p-6 rounded-xl shadow-md bg-white mb-8 border border-gray-100">
          <div className="flex items-center gap-2 mb-4 text-gray-800">
            <FaFilter className="h-5 w-5 text-purple-600" />
            <h2 className="text-xl font-semibold">Filter Anomalies</h2>
          </div>

          <div className="flex flex-wrap items-end gap-4">
            <div className="w-auto min-w-[180px]">
              <label className="block text-sm font-medium text-gray-700 mb-1">Operation Type</label>
              <select
                name="operation"
                className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                onChange={handleFilterChange}
                value={filters.operation}
              >
                <option value="">All Operations</option>
                <option value="insertion">Insertion</option>
                <option value="deletion">Deletion</option>
                <option value="update">Updation</option>
                <option value="rename">Rename</option>
              </select>
            </div>

            <div className="w-auto min-w-[180px]">
              <label className="block text-sm font-medium text-gray-700 mb-1">File Category</label>
              <select
                name="category"
                className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                onChange={handleFilterChange}
                value={filters.category}
              >
                <option value="">All Categories</option>
                {uniqueCategories.map((category, index) => (
                  <option key={index} value={category}>
                    {category}
                  </option>
                ))}
              </select>
            </div>

            <div className="w-auto min-w-[180px]">
              <label className="block text-sm font-medium text-gray-700 mb-1">Sort Order</label>
              <select
                className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                onChange={(e) => setSortOrder(e.target.value)}
                value={sortOrder}
              >
                <option value="desc">Newest First</option>
                <option value="asc">Oldest First</option>
              </select>
            </div>

            <div className="w-auto min-w-[180px]">
              <label className="block text-sm font-medium text-gray-700 mb-1">Filter on Risk</label>
              <select
                name="risk"
                className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                onChange={handleFilterChange}
                value={filters.risk || ""}
              >
                <option value="">All Risks</option>
                <option value="critical">Critical Risk</option>
                <option value="high">High Risk</option>
                <option value="medium">Medium Risk</option>
                <option value="low">Low Risk</option>
              </select>
            </div>


            <div className="w-auto min-w-[180px]">
              <label className="block text-sm font-medium text-gray-700 mb-1">Start Time</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
                  <FaCalendarAlt className="h-4 w-4 text-gray-500" />
                </div>
                <input
                  type="datetime-local"
                  name="start_time"
                  className="w-full p-2 pl-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                  onChange={handleFilterChange}
                  value={filters.start_time}
                />
              </div>
            </div>

            <div className="w-auto min-w-[180px]">
              <label className="block text-sm font-medium text-gray-700 mb-1">End Time</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
                  <FaCalendarAlt className="h-4 w-4 text-gray-500" />
                </div>
                <input
                  type="datetime-local"
                  name="end_time"
                  className="w-full p-2 pl-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                  onChange={handleFilterChange}
                  value={filters.end_time}
                />
              </div>
            </div>

            <div className="flex gap-2">
              <button
                className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors duration-300 flex items-center gap-2 h-[42px]"
                onClick={fetchAnomaliesByTime}
              >
                <FaSearch className="h-4 w-4" />
                <span>Search</span>
              </button>

              <button
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors duration-300 flex items-center gap-2 h-[42px]"
                onClick={clearFilters}
              >
                <FaTrash className="h-4 w-4" />
                <span>Clear</span>
              </button>
            </div>
          </div>
        </div>

        {/* Anomaly Table */}
        <div className="bg-white rounded-xl shadow-md border border-gray-100 overflow-hidden">
          <div className="p-4 border-b border-gray-200 bg-gray-50">
            <h2 className="text-xl font-semibold text-gray-800">Anomaly Records</h2>
            <p className="text-gray-600 text-sm">
              Showing {anomalies.length} of {totalAnomalies} total anomalies
            </p>
          </div>

          {anomalies.length === 0 ? (
            <div className="p-8 text-center">
              <p className="text-lg font-semibold text-gray-500">No anomalies found matching your criteria.</p>
              <p className="text-gray-400 mt-2">Try adjusting your filters or clearing them to see more results.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead>
                  <tr className="text-left bg-gray-50">
                    <th className="p-4 font-semibold text-gray-700 border-b">Timestamp</th>
                    <th className="p-4 font-semibold text-gray-700 border-b">IP_Address</th>
                    <th className="p-4 font-semibold text-gray-700 border-b">MAC_Address</th>
                    <th className="p-4 font-semibold text-gray-700 border-b">Operation</th>
                    <th className="p-4 font-semibold text-gray-700 border-b">File</th>
                    <th className="p-4 font-semibold text-gray-700 border-b">Category</th>
                    <th className="p-4 font-semibold text-gray-700 border-b">Risk Level</th>
                    <th className="p-4 font-semibold text-gray-700 border-b w-32">Details</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredAnomalies.map((anomaly, index) => (
                    <tr
                      key={index}
                      className="border-b border-gray-200 hover:bg-gray-50 transition-colors duration-150"
                    >
                      <td className="p-4 text-gray-700">
                        {new Date(anomaly.timestamp).toLocaleDateString("en-GB", {
                          day: "2-digit",
                          month: "2-digit",
                          year: "2-digit",
                        })}{" "}
                        {new Date(anomaly.timestamp).toLocaleTimeString("en-GB", {
                          hour: "2-digit",
                          minute: "2-digit",
                          second: "2-digit",
                          hour12: false,
                        })}
                      </td>
                      <td className="p-4 font-medium capitalize text-gray-800">{anomaly.ip_address}</td>
                      <td className="p-4 font-medium capitalize text-gray-800">{anomaly.mac_address}</td>
                      <td className={`p-4 font-semibold ${getOperationColor(anomaly.operation)}`}>
                        {anomaly.operation.charAt(0).toUpperCase() + anomaly.operation.slice(1)}
                      </td>
                      <td className="p-4 text-purple-700">{anomaly.file}</td>
                      <td className="p-4 font-medium capitalize text-gray-800">{anomaly.category}</td>

                      <td className={`p-3 font-semibold ${getRiskLevelStyle(anomaly.risk_score).color} flex items-center`}><span className={`px-2 py-1 rounded-md ${getRiskLevelStyle(anomaly.risk_score).bg}`}>
                      {getRiskLevelStyle(anomaly.risk_score).icon} {getRiskLevelStyle(anomaly.risk_score).label}
                    </span></td>



                      <td className="p-4 w-32 relative">
                        <button
                          onClick={() => toggleDropdown(index)}
                          className="text-orange-500 hover:text-orange-600 font-medium cursor-pointer text-left flex items-center gap-1"
                        >
                          <span>View Details</span>
                        </button>
                        {openDropdownId === index && (
                          <div
                            ref={(el) => (dropdownRefs.current[index] = el)}
                            className="absolute z-10 mt-2 w-72 bg-white border border-gray-200 shadow-lg rounded-lg p-4"
                            style={{
                              maxHeight: "250px",
                              overflowY: "auto",
                              left: "0",
                              top: "100%",
                            }}
                          >
                            <h4 className="font-bold text-gray-800 mb-2 pb-2 border-b">Anomaly Reasons</h4>
                            <ul className="text-sm text-gray-700 space-y-2">
                              {anomaly.reasons.map((reason, idx) => (
                                <li key={idx} className="flex items-start gap-2">
                                  <span className="text-orange-500 mt-1">•</span>
                                  <span>{reason}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Pagination */}
          <div className="flex justify-between items-center p-4 border-t border-gray-200 bg-gray-50">
            <div className="text-sm text-gray-600">
              Page {page} • {anomalies.length} records
            </div>
            <div className="flex gap-3">
              <button
                className="px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-300"
                onClick={() => setPage((prev) => Math.max(prev - 1, 1))}
                disabled={page === 1}
              >
                Previous
              </button>
              <button
                className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-300"
                onClick={() => setPage((prev) => prev + 1)}
                disabled={anomalies.length < 50}
              >
                Next
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default AnomalyDetector

