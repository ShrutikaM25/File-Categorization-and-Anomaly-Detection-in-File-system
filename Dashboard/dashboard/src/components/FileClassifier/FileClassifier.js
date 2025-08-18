"use client"

import { useState } from "react"
import { FaFolder, FaFile, FaTimes, FaUpload, FaDatabase } from "react-icons/fa"
import { CircularProgress } from "@mui/material"

const FileClassifier = () => {
  const [selectedFiles, setSelectedFiles] = useState([])
  const [loading, setLoading] = useState(false)
  const [classifiedFiles, setClassifiedFiles] = useState(null)
  const [openSnackbar, setOpenSnackbar] = useState(false)
  const [snackbarMessage, setSnackbarMessage] = useState("")
  const [directory, setDirectory] = useState(null)
  const [isDirectoryMode, setIsDirectoryMode] = useState(true)
  const [cacheData, setCacheData] = useState(null)

  const handleDirectoryChange = (event) => {
    const files = event.target.files
    const fileArray = Array.from(files)
    setSelectedFiles(fileArray)
    if (files.length > 0) {
      const path = files[0].webkitRelativePath.split("/")[0]
      setDirectory(path)
    }
  }

  const handleFileChange = (event) => {
    const files = event.target.files
    setSelectedFiles(Array.from(files))
  }

  const handleClassify = async () => {
    if (selectedFiles.length === 0) {
      setSnackbarMessage("Please select files or a directory first.")
      setOpenSnackbar(true)
      return
    }

    setLoading(true)
    const formData = new FormData()
    selectedFiles.forEach((file) => {
      formData.append("files", file)
    })

    try {
      const response = await fetch("http://127.0.0.1:5000/classify-dir", {
        method: "POST",
        body: formData,
      })

      console.log(response)

      if (!response.ok) {
        const errorData = await response.json()
        setSnackbarMessage(errorData.message || "Error classifying files.")
        setOpenSnackbar(true)
        return
      }

      const data = await response.json()
      setClassifiedFiles(data)
      setSnackbarMessage("Files classified successfully!")
      setOpenSnackbar(true)
    } catch (error) {
      setSnackbarMessage("Error classifying files. Please try again.")
      setOpenSnackbar(true)
    } finally {
      setLoading(false)
    }
  }

  const handleSnackbarClose = () => {
    setOpenSnackbar(false)
  }

  const handleFetchCache = async () => {
    try {
      const response = await fetch("http://127.0.0.1:5000/display-cache")
      const data = await response.json()
      setCacheData(data.cache_data)
    } catch (error) {
      setSnackbarMessage("Error fetching cache data.")
      setOpenSnackbar(true)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-purple-50 to-white p-6">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-4xl font-bold text-center text-gray-800 mb-6">
          File Category <span className="text-purple-700">Classifier</span>
        </h1>
        <p className="text-lg text-gray-600 text-center max-w-3xl mx-auto mb-8">
          Upload files or directories to automatically classify them into categories.
        </p>

        {/* Toggle: Directory vs. File Selection */}
        <div className="flex justify-center mt-4 mb-8">
          <button
            className={`px-6 py-3 rounded-l-lg transition font-medium ${
              isDirectoryMode ? "bg-purple-600 text-white" : "bg-white text-gray-700 border border-gray-300"
            }`}
            onClick={() => setIsDirectoryMode(true)}
          >
            Select Directory
          </button>
          <button
            className={`px-6 py-3 rounded-r-lg transition font-medium ${
              !isDirectoryMode ? "bg-purple-600 text-white" : "bg-white text-gray-700 border border-gray-300"
            }`}
            onClick={() => setIsDirectoryMode(false)}
          >
            Select Files
          </button>
        </div>

        {/* File/Directory Selection */}
        <div className="flex flex-col items-center gap-6 border py-10 px-8 rounded-xl shadow-md bg-white mt-6 mx-auto max-w-2xl">
          <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center text-purple-600 mb-2">
            <FaUpload className="h-8 w-8" />
          </div>

          {isDirectoryMode ? (
            <>
              <button
                className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-3 rounded-lg flex items-center gap-2 transition-colors duration-300 font-medium"
                type="button"
                onClick={() => document.getElementById("directory-input").click()}
              >
                <FaFolder className="h-5 w-5" />
                Select Directory
              </button>
              <input
                id="directory-input"
                type="file"
                webkitdirectory="true"
                directory="true"
                multiple
                hidden
                onChange={handleDirectoryChange}
              />
              {directory && (
                <div className="flex items-center gap-2 text-lg font-medium text-gray-700 bg-purple-50 px-4 py-2 rounded-lg">
                  <FaFolder className="text-purple-600" />
                  <p>{directory}</p>
                </div>
              )}
            </>
          ) : (
            <>
              <button
                className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-3 rounded-lg flex items-center gap-2 transition-colors duration-300 font-medium"
                type="button"
                onClick={() => document.getElementById("file-input").click()}
              >
                <FaFile className="h-5 w-5" />
                Select Files
              </button>
              <input id="file-input" type="file" multiple hidden onChange={handleFileChange} />
              {selectedFiles.length > 0 && (
                <div className="flex items-center gap-2 text-lg font-medium text-gray-700 bg-purple-50 px-4 py-2 rounded-lg">
                  <FaFile className="text-purple-600" />
                  <p>{selectedFiles.length} Files Selected</p>
                </div>
              )}
            </>
          )}

          {/* Classify Button */}
          <button
            className={`px-8 py-3 rounded-lg text-white font-medium mt-4 ${
              !selectedFiles.length || loading
                ? "bg-gray-300 cursor-not-allowed"
                : "bg-orange-500 hover:bg-orange-600 transition-colors duration-300"
            }`}
            onClick={handleClassify}
            disabled={!selectedFiles.length || loading}
          >
            {loading ? (
              <div className="flex items-center gap-2">
                <CircularProgress size={24} color="inherit" />
                <span>Processing...</span>
              </div>
            ) : (
              "Classify Files"
            )}
          </button>
        </div>

        {/* Snackbar Notification */}
        {openSnackbar && (
          <div className="fixed bottom-4 right-4 bg-green-500 text-white font-semibold px-6 py-3 rounded-lg shadow-lg flex items-center z-50">
            <p>{snackbarMessage}</p>
            <button onClick={handleSnackbarClose} className="ml-4 hover:bg-green-600 p-1 rounded">
              <FaTimes />
            </button>
          </div>
        )}

        {/* Display Classified Files */}
        {classifiedFiles && (
          <div className="mt-16">
            <h2 className="text-3xl font-bold text-center text-gray-800 mb-8">Classification Results</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mt-8">
              {Object.keys(classifiedFiles).map((category) => {
                const displayCategory = category.includes("Prediction error") || !category ? "Unknown" : category
                return (
                  <div key={category} className="bg-white shadow-lg rounded-xl overflow-hidden border border-gray-100">
                    <div className="bg-purple-600 text-white p-4">
                      <h3 className="text-xl font-bold">{displayCategory}</h3>
                    </div>
                    <ul className="p-6 text-gray-700 divide-y divide-gray-100">
                      {classifiedFiles[category].map((file, index) => (
                        <li key={index} className="flex items-center gap-3 py-3">
                          <FaFile className="text-purple-500 flex-shrink-0" />
                          <span className="truncate">{file.file}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* Fetch Cache Button */}
        <div className="mt-12 flex justify-center">
          <button
            className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-3 rounded-lg flex items-center gap-2 transition-colors duration-300 font-medium"
            onClick={handleFetchCache}
          >
            <FaDatabase className="h-5 w-5" />
            Fetch Cache Data
          </button>
        </div>
      </div>
    </div>
  )
}

export default FileClassifier

