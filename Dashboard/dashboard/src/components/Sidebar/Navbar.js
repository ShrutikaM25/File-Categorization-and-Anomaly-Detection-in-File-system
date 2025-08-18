import React, { useState, useEffect, useRef } from "react";
import { BiBell } from "react-icons/bi";
import { IoIosCloseCircle } from "react-icons/io";
import { motion, AnimatePresence } from "framer-motion";

import HighPriority from '../../utils/high_priority.mp3';
import MediumPriority from '../../utils/medium_priority.mp3';
import LowPriority from '../../utils/low_priority.mp3';
const Navbar = ({ toggleSidebar }) => {
  const [showNotifications, setShowNotifications] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const notificationRef = useRef(null);

  const highPriorityAudio = useRef(new Audio(HighPriority));
  const mediumPriorityAudio = useRef(new Audio(MediumPriority));
  const lowPriorityAudio = useRef(new Audio(LowPriority));

  // Close notifications when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (notificationRef.current && !notificationRef.current.contains(event.target)) {
        setShowNotifications(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const playNotificationSound = (severity) => {
    switch (severity) {
      case "high":
        highPriorityAudio.current.play().catch(e => console.log("Audio playback failed:", e));
        break;
      case "medium":
        mediumPriorityAudio.current.play().catch(e => console.log("Audio playback failed:", e));
        break;
      default:
        lowPriorityAudio.current.play().catch(e => console.log("Audio playback failed:", e));
    }
  };
  // Handle SSE connection for real-time notifications
  useEffect(() => {
    const eventSource = new EventSource("http://127.0.0.1:5000/events");
    
    eventSource.onmessage = (event) => {
      try {
        const newAnomalies = JSON.parse(event.data);
        console.log("Received Anomalies:", newAnomalies);

        if (newAnomalies.length > 0) {
          // Determine highest severity level in the batch
          const highestSeverity = newAnomalies.reduce((max, anomaly) => {
            const severity = getSeverity(anomaly.operation);
            return severity === "high" ? "high" : severity === "medium" && max !== "high" ? "medium" : max;
          }, "low");

          playNotificationSound(highestSeverity);
          
          // Show desktop notification if allowed
          if (Notification.permission === "granted") {
            new Notification("New Security Alert", {
              body:`New ${highestSeverity.toUpperCase()} priority anomalies detected` ,
              icon: "/alert-icon.png"
            });
          }

          // Create notification objects
          const newNotifications = newAnomalies.map(anomaly => ({
            id: Date.now() + Math.random(),
            message: `🚨 ${(anomaly.operation || "Unknown Operation").toUpperCase()} detected on ${anomaly.file || "Unknown File"}`,
            timestamp: anomaly.timestamp 
              ? new Date(anomaly.timestamp).toLocaleTimeString() 
              : "Unknown Time",
            read: false,
            severity: getSeverity(anomaly.operation)
          }));

          setNotifications(prev => [...newNotifications, ...prev]);
          setUnreadCount(prev => prev + newNotifications.length);
        }
      } catch (error) {
        console.error("Error processing SSE event:", error);
      }
    };

    if (Notification.permission !== "granted" && Notification.permission !== "denied") {
      Notification.requestPermission();
    }

    return () => eventSource.close();
  }, []);

  const getSeverity = (operation) => {
    const highSeverityOps = ["delete", "modify", "encrypt"];
    const mediumSeverityOps = ["move", "rename", "permission change"];
    
    if (highSeverityOps.some(op => operation?.toLowerCase().includes(op))) {
      return "high";
    } else if (mediumSeverityOps.some(op => operation?.toLowerCase().includes(op))) {
      return "medium";
    }
    return "low";
  };

  // Mark all notifications as read
  const markAllAsRead = () => {
    setNotifications(notifications.map(notif => ({ ...notif, read: true })));
    setUnreadCount(0);
  };

  // Remove a specific notification
  const removeNotification = (id) => {
    setNotifications(prev => {
    const updatedNotifications = prev.filter(n => n.id !== id);
    const unreadRemoved = prev.find(n => n.id === id && !n.read);
    if (unreadRemoved) {
      setUnreadCount((count) => Math.max(0, count - 1));
      setShowNotifications(false);
    }

    return updatedNotifications;
    });
  };

  const clearAllNotifications = () => {
    setNotifications([]);
    setUnreadCount(0);
    setShowNotifications(false);
  };

  // Get severity color
  const getSeverityColor = (severity) => {
    switch (severity) {
      case "high": return "bg-red-100 border-l-4 border-red-500";
      case "medium": return "bg-orange-100 border-l-4 border-orange-500";
      default: return "bg-blue-100 border-l-4 border-blue-500";
    }
  };

  return (
    <nav className="bg-purple-900 text-white px-4 py-3 flex items-center justify-between fixed w-full h-16 top-0 left-0 shadow-md z-50">
      {/* Sidebar Toggle Button (Mobile) */}
      <button className="md:hidden text-white" onClick={toggleSidebar}>
        {/* <Menu size={24} /> */}
      </button>

      {/* App Name */}
      <h1 className="text-xl font-semibold">Anomaly Detector</h1>

      <div className="relative" ref={notificationRef}>
        <button 
          onClick={() => {
            setShowNotifications(!showNotifications);
            if (!showNotifications && unreadCount > 0) {
              markAllAsRead();
            }
          }} 
          className="relative p-2 hover:bg-purple-800 rounded-full transition-colors duration-200"
          aria-label="Notifications"
        >
          <BiBell size={24} />
          
          {/* Notification Badge with Animation */}
          <AnimatePresence>
            {unreadCount > 0 && (
              <motion.span 
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                exit={{ scale: 0 }}
                className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center"
              >
                {unreadCount > 9 ? '9+' : unreadCount}
              </motion.span>
            )}
          </AnimatePresence>
        </button>

        {/* Notification Panel */}
        <AnimatePresence>
          {showNotifications && (
            <motion.div 
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.2 }}
              className="absolute right-0 mt-2 w-96 bg-white shadow-lg rounded-lg overflow-hidden text-black max-h-96 flex flex-col"
            >
              <div className="flex justify-between items-center border-b p-3 bg-gray-50">
                <h3 className="text-lg font-semibold">Notifications</h3>
                <div className="flex gap-2">
                  {notifications.length > 0 && (
                    <button 
                      onClick={clearAllNotifications}
                      className="text-sm text-gray-500 hover:text-gray-700"
                    >
                      Clear all
                    </button>
                  )}
                  <button onClick={() => setShowNotifications(false)}>
                    <IoIosCloseCircle size={20} className="text-gray-500 hover:text-gray-700" />
                  </button>
                </div>
              </div>

              {/* Notification List with Scroll */}
              <div className="overflow-y-auto max-h-80 flex-grow">
                {notifications.length === 0 ? (
                  <div className="flex flex-col items-center justify-center h-32 text-gray-500">
                    <BiBell size={36} />
                    <p className="mt-2">No notifications</p>
                  </div>
                ) : (
                  <div>
                    {notifications.map((notification) => (
                      <motion.div 
                        key={notification.id}
                        initial={{ x: 50, opacity: 0 }}
                        animate={{ x: 0, opacity: 1 }}
                        exit={{ x: -50, opacity: 0 }}
                        className={`p-3 m-2 rounded-lg relative ${getSeverityColor(notification.severity)}`}
                      >
                        <button 
                          onClick={() => removeNotification(notification.id)}
                          className="absolute top-2 right-2 text-gray-400 hover:text-gray-600"
                          aria-label="Dismiss notification"
                        >
                          <IoIosCloseCircle size={16} />
                        </button>
                        <p className="text-sm pr-6">{notification.message}</p>
                        <div className="flex justify-between items-center mt-1">
                          <span className="text-xs text-gray-500">{notification.timestamp}</span>
                          {!notification.read && (
                            <span className="text-xs bg-blue-500 text-white px-1.5 py-0.5 rounded-full">New</span>
                          )}
                        </div>
                      </motion.div>
                    ))}
                  </div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </nav>
  );
};

export default Navbar;