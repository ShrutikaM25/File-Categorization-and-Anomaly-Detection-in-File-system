
import { FiBell, FiBarChart2, FiFileText, FiMonitor, FiArrowRight, FiShield, FiUsers, FiClock } from "react-icons/fi"
import { Link } from "react-router-dom";

export default function Home() {


  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-b from-purple-50 to-white">
      {/* Navigation */}
      {/* <nav className="w-full py-4 px-6 md:px-12 flex justify-between items-center bg-white shadow-sm">
        <div className="flex items-center">
          <div className="h-10 w-10 rounded-lg bg-gradient-to-br from-purple-600 to-indigo-700 flex items-center justify-center text-white font-bold text-xl">
            AD
          </div>
          <span className="ml-3 text-xl font-semibold text-gray-800">AnomalyDetect</span>
        </div>
        <div className="hidden md:flex space-x-6 items-center">
          <a href="#features" className="text-gray-600 hover:text-purple-700 transition-colors">Features</a>
          <a href="#testimonials" className="text-gray-600 hover:text-purple-700 transition-colors">Testimonials</a>
          <a href="#pricing" className="text-gray-600 hover:text-purple-700 transition-colors">Pricing</a>
          <button
            // onClick={handleCTAClick}
            className="bg-purple-600 hover:bg-purple-700 text-white font-medium py-2 px-4 rounded-lg transition-colors duration-300"
          >
            Login
          </button>
        </div>
        <button className="md:hidden text-gray-700">
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
      </nav> */}

      {/* Hero Section */}
      <section className="w-full py-16 md:py-24 px-6 md:px-12 flex flex-col md:flex-row items-center justify-between max-w-7xl mx-auto">
        <div className="md:w-1/2 mb-10 md:mb-0">
          <h1 className="text-4xl md:text-5xl font-bold text-gray-800 leading-tight mb-6">
            Advanced <span className="text-purple-700">Anomaly Detection</span> for Modern Systems
          </h1>
          <p className="text-lg text-gray-600 mb-8 leading-relaxed">
            Our intelligent system provides real-time anomaly detection and advanced analytics
            to help you quickly identify, analyze, and resolve critical issues before they impact your business.
          </p>
          <div className="flex flex-col sm:flex-row gap-4">
           <Link to="/dashboard">
           <button
              // onClick={handleCTAClick}
              className="bg-purple-600 hover:bg-purple-700 text-white font-semibold py-3 px-8 rounded-lg transition-colors duration-300 flex items-center justify-center"
            >
              Get Started <FiArrowRight className="ml-2" />
            </button>
           </Link>
            <button
              className="border border-purple-600 text-purple-600 hover:bg-purple-50 font-semibold py-3 px-8 rounded-lg transition-colors duration-300"
            >
              Watch Demo
            </button>
          </div>
        </div>
        <div className="md:w-1/2 flex justify-center">
          <div className="relative">
            <div className="absolute -inset-1 rounded-lg bg-gradient-to-r from-purple-600 to-indigo-600 opacity-30 blur-lg"></div>
            <div className="relative bg-white p-6 rounded-lg shadow-xl">
              <img
                src="https://static.vecteezy.com/system/resources/previews/034/988/914/non_2x/2d-gradient-icon-anomaly-detection-concept-isolated-predictive-maintenance-thin-line-illustration-vector.jpg"
                alt="Anomaly Detection Dashboard"
                className="w-full h-auto rounded"
              />
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="w-full py-12 bg-purple-800">
        <div className="max-w-7xl mx-auto px-6 md:px-12">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
            <div className="flex flex-col items-center">
              <span className="text-4xl font-bold text-white mb-2">99.9%</span>
              <span className="text-purple-200">Detection Accuracy</span>
            </div>
            <div className="flex flex-col items-center">
              <span className="text-4xl font-bold text-white mb-2">500+</span>
              <span className="text-purple-200">Enterprise Clients</span>
            </div>
            <div className="flex flex-col items-center">
              <span className="text-4xl font-bold text-white mb-2">24/7</span>
              <span className="text-purple-200">Monitoring</span>
            </div>
            <div className="flex flex-col items-center">
              <span className="text-4xl font-bold text-white mb-2">5min</span>
              <span className="text-purple-200">Avg. Response Time</span>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="w-full py-16 md:py-24 px-6 md:px-12 bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-800 mb-4">Why Choose Our System?</h2>
            <p className="text-lg text-gray-600 max-w-3xl mx-auto">
              Our comprehensive anomaly detection platform provides everything you need to monitor,
              detect, and respond to issues in real-time.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            <div className="bg-white p-6 rounded-xl shadow-md hover:shadow-lg transition-shadow border border-gray-100 flex flex-col items-center text-center">
              <div className="w-14 h-14 bg-purple-100 rounded-full flex items-center justify-center text-purple-600 mb-4">
                <FiBell className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-semibold text-gray-800 mb-3">Real-Time Alerts</h3>
              <p className="text-gray-600">
                Receive immediate notifications as anomalies are detected, ensuring you stay informed of critical issues.
              </p>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-md hover:shadow-lg transition-shadow border border-gray-100 flex flex-col items-center text-center">
              <div className="w-14 h-14 bg-purple-100 rounded-full flex items-center justify-center text-purple-600 mb-4">
                <FiBarChart2 className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-semibold text-gray-800 mb-3">Actionable Insights</h3>
              <p className="text-gray-600">
                Gain detailed insights through advanced analytics and visualizations to drive quick resolutions.
              </p>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-md hover:shadow-lg transition-shadow border border-gray-100 flex flex-col items-center text-center">
              <div className="w-14 h-14 bg-purple-100 rounded-full flex items-center justify-center text-purple-600 mb-4">
                <FiFileText className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-semibold text-gray-800 mb-3">Comprehensive Reporting</h3>
              <p className="text-gray-600">
                Access in-depth reports and trend analyses to understand the full context of anomalies.
              </p>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-md hover:shadow-lg transition-shadow border border-gray-100 flex flex-col items-center text-center">
              <div className="w-14 h-14 bg-purple-100 rounded-full flex items-center justify-center text-purple-600 mb-4">
                <FiMonitor className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-semibold text-gray-800 mb-3">User-Friendly Interface</h3>
              <p className="text-gray-600">
                Navigate through intuitive dashboards designed to provide clarity and ease of use.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="w-full py-16 md:py-24 px-6 md:px-12 bg-gray-50">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-800 mb-4">How It Works</h2>
            <p className="text-lg text-gray-600 max-w-3xl mx-auto">
              Our platform uses advanced machine learning algorithms to detect anomalies in your data
              and provide actionable insights.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="relative">
              <div className="absolute top-0 left-1/2 -translate-x-1/2 w-10 h-10 bg-purple-600 text-white rounded-full flex items-center justify-center font-bold z-10">1</div>
              <div className="pt-12 pb-6 px-6 bg-white rounded-xl shadow-md border border-gray-100 text-center relative">
                <div className="w-16 h-16 mx-auto bg-purple-100 rounded-full flex items-center justify-center text-purple-600 mb-4">
                  <FiShield className="w-8 h-8" />
                </div>
                <h3 className="text-xl font-semibold text-gray-800 mb-3">Connect Your Systems</h3>
                <p className="text-gray-600">
                  Easily integrate our platform with your existing systems using our secure API connections.
                </p>
              </div>
            </div>

            <div className="relative">
              <div className="absolute top-0 left-1/2 -translate-x-1/2 w-10 h-10 bg-purple-600 text-white rounded-full flex items-center justify-center font-bold z-10">2</div>
              <div className="pt-12 pb-6 px-6 bg-white rounded-xl shadow-md border border-gray-100 text-center relative">
                <div className="w-16 h-16 mx-auto bg-purple-100 rounded-full flex items-center justify-center text-purple-600 mb-4">
                  <FiClock className="w-8 h-8" />
                </div>
                <h3 className="text-xl font-semibold text-gray-800 mb-3">Real-Time Monitoring</h3>
                <p className="text-gray-600">
                  Our system continuously monitors your data streams to detect anomalies as they occur.
                </p>
              </div>
            </div>

            <div className="relative">
              <div className="absolute top-0 left-1/2 -translate-x-1/2 w-10 h-10 bg-purple-600 text-white rounded-full flex items-center justify-center font-bold z-10">3</div>
              <div className="pt-12 pb-6 px-6 bg-white rounded-xl shadow-md border border-gray-100 text-center relative">
                <div className="w-16 h-16 mx-auto bg-purple-100 rounded-full flex items-center justify-center text-purple-600 mb-4">
                  <FiUsers className="w-8 h-8" />
                </div>
                <h3 className="text-xl font-semibold text-gray-800 mb-3">Take Action</h3>
                <p className="text-gray-600">
                  Receive alerts and insights that enable your team to respond quickly to potential issues.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>



      {/* CTA Section */}
      <section className="w-full py-16 md:py-24 px-6 md:px-12 bg-gradient-to-r from-purple-700 to-indigo-800 text-white">
        <div className="max-w-7xl mx-auto text-center">
          <h2 className="text-3xl md:text-4xl font-bold mb-6">Ready to Transform Your Anomaly Detection?</h2>
          <p className="text-xl text-purple-100 mb-8 max-w-3xl mx-auto">
            Join hundreds of companies that trust our platform to keep their systems running smoothly.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link to="/dashboard">            <button

              className="bg-white text-purple-700 hover:bg-purple-50 font-semibold py-3 px-8 rounded-lg transition-colors duration-300"
            >
              Get Started Now
            </button></Link>
            
          </div>
        </div>
      </section>


    </div>

  );
}
