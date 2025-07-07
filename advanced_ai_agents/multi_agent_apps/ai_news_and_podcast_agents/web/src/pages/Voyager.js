import React, { useState, useEffect } from 'react';
import api from '../services/api';
import TaskForm from '../components/TaskForm';
import PodcastConfigForm from '../components/PodcastConfigForm';

const Voyager = () => {
   const [tasks, setTasks] = useState([]);
   const [taskExecutions, setTaskExecutions] = useState([]);
   const [loading, setLoading] = useState(true);
   const [error, setError] = useState(null);
   const [activeTab, setActiveTab] = useState('tasks');
   const [isModalOpen, setIsModalOpen] = useState(false);
   const [currentTask, setCurrentTask] = useState(null);
   const [viewOutputModal, setViewOutputModal] = useState(false);
   const [currentOutput, setCurrentOutput] = useState('');
   const [currentOutputTaskName, setCurrentOutputTaskName] = useState('');
   const [executionsPage, setExecutionsPage] = useState(1);
   const [executionsPerPage, setExecutionsPerPage] = useState(10);
   const [executionsTotalPages, setExecutionsTotalPages] = useState(0);
   const [executionsTotal, setExecutionsTotal] = useState(0);
   const [executionsHasNext, setExecutionsHasNext] = useState(false);
   const [executionsHasPrev, setExecutionsHasPrev] = useState(false);
   const [selectedTaskId, setSelectedTaskId] = useState(null);
   const [podcastConfigs, setPodcastConfigs] = useState([]);
   const [isConfigModalOpen, setIsConfigModalOpen] = useState(false);
   const [currentConfig, setCurrentConfig] = useState(null);

   const loadTasks = async () => {
      setLoading(true);
      setError(null);
      try {
         const response = await api.tasks.getAll(true);
         setTasks(response.data);
      } catch (err) {
         console.error('Error fetching tasks:', err);
         setError('Failed to load tasks: ' + (err.message || 'Unknown error'));
      } finally {
         setLoading(false);
      }
   };

   const loadPodcastConfigs = async () => {
      setLoading(true);
      setError(null);
      try {
         const response = await api.podcastConfigs.getAll(false);
         setPodcastConfigs(response.data);
      } catch (err) {
         console.error('Error fetching podcast configs:', err);
         setError('Failed to load podcast configurations: ' + (err.message || 'Unknown error'));
      } finally {
         setLoading(false);
      }
   };

   const loadTaskExecutions = async (taskId = null, page = 1) => {
      setLoading(true);
      try {
         const response = await api.tasks.getExecutions({
            taskId,
            page,
            perPage: executionsPerPage,
         });
         const data = response.data;
         setTaskExecutions(data.items || []);
         setExecutionsPage(data.page || 1);
         setExecutionsTotalPages(data.total_pages || 0);
         setExecutionsTotal(data.total || 0);
         setExecutionsHasNext(data.has_next || false);
         setExecutionsHasPrev(data.has_prev || false);
         setSelectedTaskId(taskId);
      } catch (err) {
         console.error('Error fetching task executions:', err);
         setError('Failed to load task executions: ' + (err.message || 'Unknown error'));
      } finally {
         setLoading(false);
      }
   };

   useEffect(() => {
      if (activeTab === 'tasks') {
         loadTasks();
      } else if (activeTab === 'executions') {
         loadTaskExecutions(selectedTaskId, executionsPage);
      } else if (activeTab === 'podcast-configs') {
         loadPodcastConfigs();
      }
   }, [activeTab]);

   const handleExecutionsPageChange = newPage => {
      setExecutionsPage(newPage);
      loadTaskExecutions(selectedTaskId, newPage);
   };

   const handleFilterByTask = async taskId => {
      setSelectedTaskId(taskId);
      setExecutionsPage(1);
      await loadTaskExecutions(taskId, 1);
   };

   const handleClearTaskFilter = async () => {
      setSelectedTaskId(null);
      setExecutionsPage(1);
      await loadTaskExecutions(null, 1);
   };

   const handleTaskToggle = async (taskId, isEnabled) => {
      try {
         if (isEnabled) {
            await api.tasks.disable(taskId);
         } else {
            await api.tasks.enable(taskId);
         }
         setTasks(prevTasks =>
            prevTasks.map(task => (task.id === taskId ? { ...task, enabled: !isEnabled } : task))
         );
      } catch (err) {
         console.error('Error toggling task:', err);
         alert('Failed to update task: ' + (err.message || 'Unknown error'));
      }
   };

   const handleConfigToggle = async (configId, isActive) => {
      try {
         await api.podcastConfigs.toggle(configId, !isActive);
         setPodcastConfigs(prevConfigs =>
            prevConfigs.map(config =>
               config.id === configId ? { ...config, is_active: !isActive } : config
            )
         );
      } catch (err) {
         console.error('Error toggling podcast config:', err);
         alert('Failed to update podcast configuration: ' + (err.message || 'Unknown error'));
      }
   };

   const handleViewOutput = (output, taskName) => {
      setCurrentOutput(output || 'No output available');
      setCurrentOutputTaskName(taskName);
      setViewOutputModal(true);
   };

   const handleCloseOutputModal = () => {
      setViewOutputModal(false);
      setCurrentOutput('');
      setCurrentOutputTaskName('');
   };

   const handleTaskDelete = async taskId => {
      if (!window.confirm('Are you sure you want to delete this task?')) {
         return;
      }
      try {
         await api.tasks.delete(taskId);
         setTasks(prevTasks => prevTasks.filter(task => task.id !== taskId));
      } catch (err) {
         console.error('Error deleting task:', err);
         alert('Failed to delete task: ' + (err.message || 'Unknown error'));
      }
   };

   const handleConfigDelete = async configId => {
      if (!window.confirm('Are you sure you want to delete this podcast configuration?')) {
         return;
      }
      try {
         await api.podcastConfigs.delete(configId);
         setPodcastConfigs(prevConfigs => prevConfigs.filter(config => config.id !== configId));
      } catch (err) {
         console.error('Error deleting podcast config:', err);
         alert('Failed to delete podcast configuration: ' + (err.message || 'Unknown error'));
      }
   };

   const handleNewTask = () => {
      setCurrentTask(null);
      setIsModalOpen(true);
   };

   const handleEditTask = task => {
      setCurrentTask(task);
      setIsModalOpen(true);
   };

   const handleNewConfig = () => {
      setCurrentConfig(null);
      setIsConfigModalOpen(true);
   };

   const handleEditConfig = config => {
      setCurrentConfig(config);
      setIsConfigModalOpen(true);
   };

   const handleCloseModal = () => {
      setIsModalOpen(false);
      setCurrentTask(null);
   };

   const handleCloseConfigModal = () => {
      setIsConfigModalOpen(false);
      setCurrentConfig(null);
   };

   const handleTaskSubmit = async taskData => {
      try {
         if (currentTask) {
            await api.tasks.update(currentTask.id, taskData);
         } else {
            await api.tasks.create(taskData);
         }
         await loadTasks();
         handleCloseModal();
      } catch (err) {
         console.error('Error saving task:', err);
         throw err;
      }
   };

   const handleConfigSubmit = async configData => {
      try {
         if (currentConfig) {
            await api.podcastConfigs.update(currentConfig.id, configData);
         } else {
            await api.podcastConfigs.create(configData);
         }
         await loadPodcastConfigs();
         handleCloseConfigModal();
      } catch (err) {
         console.error('Error saving podcast config:', err);
         throw err;
      }
   };

   const formatDate = dateString => {
      if (!dateString) return 'Never';
      return new Date(dateString).toLocaleString();
   };

   const getStatusClass = status => {
      switch (status) {
         case 'success':
            return 'text-emerald-400';
         case 'failed':
            return 'text-red-400';
         case 'running':
            return 'text-blue-400';
         default:
            return 'text-gray-400';
      }
   };

   const ToggleSwitch = ({ enabled, onChange }) => {
      return (
         <button
            onClick={onChange}
            className="relative inline-flex h-6 w-11 items-center rounded-full focus:outline-none"
            aria-pressed={enabled}
         >
            <span className="sr-only">{enabled ? 'Disable' : 'Enable'}</span>
            <span
               className={`absolute inline-block h-5 w-10 rounded-full transition-colors ${
                  enabled ? 'bg-emerald-500' : 'bg-gray-600'
               }`}
            />
            <span
               className={`absolute inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  enabled ? 'translate-x-5' : 'translate-x-1'
               }`}
            />
         </button>
      );
   };

   return (
      <div className="max-w-6xl mx-auto">
         <h1 className="text-2xl font-medium text-gray-100 mb-6 flex items-center">
            <div className="h-10 w-10 mr-3 flex items-center justify-center relative">
               <svg
                  className="w-10 h-10 text-emerald-500 relative z-10"
                  viewBox="0 0 100 100"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                  stroke="currentColor"
                  strokeWidth="4.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
               >
                  <circle cx="50" cy="50" r="35" />
                  <path d="M30 70 A 35 35 0 0 1 70 70" />
                  <line x1="50" y1="50" x2="35" y2="35" strokeWidth="1.5" />
                  <circle cx="50" cy="50" r="5" fill="currentColor" />
               </svg>
               <div className="absolute inset-0 bg-emerald-500 opacity-30 blur-md rounded-full"></div>
            </div>
            Voyager
         </h1>
         <div className="flex border-b border-gray-700 mb-6">
            <button
               className={`py-2 px-4 text-sm font-medium border-b-2 ${
                  activeTab === 'tasks'
                     ? 'text-emerald-400 border-emerald-400'
                     : 'text-gray-400 border-transparent hover:text-gray-300 hover:border-gray-600'
               } transition-colors duration-200`}
               onClick={() => setActiveTab('tasks')}
            >
               Tasks
            </button>
            <button
               className={`py-2 px-4 text-sm font-medium border-b-2 ${
                  activeTab === 'podcast-configs'
                     ? 'text-emerald-400 border-emerald-400'
                     : 'text-gray-400 border-transparent hover:text-gray-300 hover:border-gray-600'
               } transition-colors duration-200`}
               onClick={() => setActiveTab('podcast-configs')}
            >
               Podcast Configs
            </button>
            <button
               className={`py-2 px-4 text-sm font-medium border-b-2 ${
                  activeTab === 'executions'
                     ? 'text-emerald-400 border-emerald-400'
                     : 'text-gray-400 border-transparent hover:text-gray-300 hover:border-gray-600'
               } transition-colors duration-200`}
               onClick={() => {
                  setActiveTab('executions');
                  loadTaskExecutions(selectedTaskId, 1);
               }}
            >
               Executions
            </button>
         </div>
         {error && (
            <div className="bg-gradient-to-br from-gray-800 to-gray-900 shadow-lg rounded-sm overflow-hidden border border-red-700 p-4 mb-6">
               <div className="flex">
                  <div className="flex-shrink-0">
                     <svg
                        className="h-5 w-5 text-red-400"
                        xmlns="http://www.w3.org/2000/svg"
                        viewBox="0 0 20 20"
                        fill="currentColor"
                     >
                        <path
                           fillRule="evenodd"
                           d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                           clipRule="evenodd"
                        />
                     </svg>
                  </div>
                  <div className="ml-3">
                     <p className="text-sm text-red-400">{error}</p>
                  </div>
               </div>
            </div>
         )}
         {activeTab === 'tasks' && (
            <div className="bg-gradient-to-br from-gray-800 to-gray-900 shadow-lg rounded-sm overflow-hidden border border-gray-700">
               <div className="h-0.5 w-full bg-gradient-to-r from-transparent via-emerald-800 to-transparent opacity-60"></div>
               <div className="p-4">
                  <div className="flex justify-between items-center mb-4">
                     <h3 className="text-lg font-medium text-gray-200">System Tasks</h3>
                     <div className="flex space-x-2">
                        <button
                           onClick={loadTasks}
                           className="px-3 py-1.5 text-sm rounded-sm bg-gradient-to-r from-gray-700 to-gray-800 text-gray-300 border border-gray-700 hover:border-gray-600 transition-colors duration-200"
                        >
                           Refresh
                        </button>
                        <button
                           onClick={handleNewTask}
                           className="px-3 py-1.5 text-sm rounded-sm bg-gradient-to-r from-emerald-700 to-emerald-800 text-white border border-emerald-600 hover:from-emerald-600 hover:to-emerald-700 transition-colors duration-200"
                        >
                           New Task
                        </button>
                     </div>
                  </div>
                  {loading ? (
                     <div className="flex justify-center py-20">
                        <div className="w-12 h-12 border-4 border-emerald-600 border-t-transparent rounded-full animate-spin"></div>
                     </div>
                  ) : (
                     <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-700">
                           <thead className="bg-gradient-to-r from-gray-900 to-gray-800">
                              <tr>
                                 <th
                                    scope="col"
                                    className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider"
                                 >
                                    Task
                                 </th>
                                 <th
                                    scope="col"
                                    className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider"
                                 >
                                    Command
                                 </th>
                                 <th
                                    scope="col"
                                    className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider"
                                 >
                                    Schedule
                                 </th>
                                 <th
                                    scope="col"
                                    className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider"
                                 >
                                    Status
                                 </th>
                                 <th
                                    scope="col"
                                    className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider"
                                 >
                                    Last Run
                                 </th>
                                 <th
                                    scope="col"
                                    className="px-4 py-3 text-right text-xs font-medium text-gray-400 uppercase tracking-wider"
                                 >
                                    Actions
                                 </th>
                              </tr>
                           </thead>
                           <tbody className="divide-y divide-gray-700">
                              {tasks.map(task => (
                                 <tr
                                    key={task.id}
                                    className="hover:bg-gray-800 transition-all duration-200"
                                 >
                                    <td className="px-4 py-3 whitespace-nowrap">
                                       <div className="text-sm font-medium text-gray-200">
                                          {task.name}
                                       </div>
                                       {task.description && (
                                          <div className="text-xs text-gray-500 mt-1">
                                             {task.description}
                                          </div>
                                       )}
                                    </td>
                                    <td className="px-4 py-3">
                                       <div className="text-sm text-gray-300 font-mono truncate max-w-xs">
                                          {task.command}
                                       </div>
                                    </td>
                                    <td className="px-4 py-3 whitespace-nowrap">
                                       <span className="px-2 py-0.5 text-xs rounded-sm bg-gradient-to-r from-gray-900 to-gray-800 text-emerald-300 border border-gray-700">
                                          Every {task.frequency} {task.frequency_unit}
                                       </span>
                                    </td>
                                    <td className="px-4 py-3 whitespace-nowrap">
                                       <div className="flex items-center">
                                          <ToggleSwitch
                                             enabled={task.enabled}
                                             onChange={() =>
                                                handleTaskToggle(task.id, task.enabled)
                                             }
                                          />
                                          <span
                                             className={`ml-2 text-sm ${
                                                task.enabled ? 'text-emerald-400' : 'text-gray-500'
                                             }`}
                                          >
                                             {task.enabled ? 'Enabled' : 'Disabled'}
                                          </span>
                                       </div>
                                    </td>
                                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-400">
                                       {formatDate(task.last_run)}
                                    </td>
                                    <td className="px-4 py-3 whitespace-nowrap text-right text-sm font-medium">
                                       <div className="flex justify-end space-x-2">
                                          <button
                                             onClick={() => handleEditTask(task)}
                                             className="text-gray-400 hover:text-blue-400 transition-colors duration-200"
                                             title="Edit"
                                          >
                                             <svg
                                                xmlns="http://www.w3.org/2000/svg"
                                                className="h-5 w-5"
                                                fill="none"
                                                viewBox="0 0 24 24"
                                                stroke="currentColor"
                                             >
                                                <path
                                                   strokeLinecap="round"
                                                   strokeLinejoin="round"
                                                   strokeWidth={2}
                                                   d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                                                />
                                             </svg>
                                          </button>
                                          <button
                                             onClick={() => handleTaskDelete(task.id)}
                                             className="text-gray-400 hover:text-red-400 transition-colors duration-200"
                                             title="Delete"
                                          >
                                             <svg
                                                xmlns="http://www.w3.org/2000/svg"
                                                className="h-5 w-5"
                                                fill="none"
                                                viewBox="0 0 24 24"
                                                stroke="currentColor"
                                             >
                                                <path
                                                   strokeLinecap="round"
                                                   strokeLinejoin="round"
                                                   strokeWidth={2}
                                                   d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                                                />
                                             </svg>
                                          </button>
                                       </div>
                                    </td>
                                 </tr>
                              ))}
                           </tbody>
                        </table>
                        {tasks.length === 0 && !loading && (
                           <div className="text-center py-8 text-gray-500">No tasks found</div>
                        )}
                     </div>
                  )}
               </div>
            </div>
         )}
         {activeTab === 'podcast-configs' && (
            <div className="bg-gradient-to-br from-gray-800 to-gray-900 shadow-lg rounded-sm overflow-hidden border border-gray-700">
               <div className="h-0.5 w-full bg-gradient-to-r from-transparent via-emerald-800 to-transparent opacity-60"></div>
               <div className="p-4">
                  <div className="flex justify-between items-center mb-4">
                     <h3 className="text-lg font-medium text-gray-200">Podcast Configurations</h3>
                     <div className="flex space-x-2">
                        <button
                           onClick={loadPodcastConfigs}
                           className="px-3 py-1.5 text-sm rounded-sm bg-gradient-to-r from-gray-700 to-gray-800 text-gray-300 border border-gray-700 hover:border-gray-600 transition-colors duration-200"
                        >
                           Refresh
                        </button>
                        <button
                           onClick={handleNewConfig}
                           className="px-3 py-1.5 text-sm rounded-sm bg-gradient-to-r from-emerald-700 to-emerald-800 text-white border border-emerald-600 hover:from-emerald-600 hover:to-emerald-700 transition-colors duration-200"
                        >
                           New Configuration
                        </button>
                     </div>
                  </div>
                  {loading ? (
                     <div className="flex justify-center py-20">
                        <div className="w-12 h-12 border-4 border-emerald-600 border-t-transparent rounded-full animate-spin"></div>
                     </div>
                  ) : (
                     <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-700">
                           <thead className="bg-gradient-to-r from-gray-900 to-gray-800">
                              <tr>
                                 <th
                                    scope="col"
                                    className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider"
                                 >
                                    Configuration
                                 </th>
                                 <th
                                    scope="col"
                                    className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider"
                                 >
                                    Search Prompt
                                 </th>
                                 <th
                                    scope="col"
                                    className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider"
                                 >
                                    Settings
                                 </th>
                                 <th
                                    scope="col"
                                    className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider"
                                 >
                                    Status
                                 </th>
                                 <th
                                    scope="col"
                                    className="px-4 py-3 text-right text-xs font-medium text-gray-400 uppercase tracking-wider"
                                 >
                                    Actions
                                 </th>
                              </tr>
                           </thead>
                           <tbody className="divide-y divide-gray-700">
                              {podcastConfigs.map(config => (
                                 <tr
                                    key={config.id}
                                    className="hover:bg-gray-800 transition-all duration-200"
                                 >
                                    <td className="px-4 py-3 whitespace-nowrap">
                                       <div className="text-sm font-medium text-gray-200">
                                          {config.name}
                                       </div>
                                       {config.description && (
                                          <div className="text-xs text-gray-500 mt-1">
                                             {config.description}
                                          </div>
                                       )}
                                    </td>
                                    <td className="px-4 py-3">
                                       <div className="text-sm text-gray-300 truncate max-w-xs">
                                          {config.prompt}
                                       </div>
                                    </td>
                                    <td className="px-4 py-3 whitespace-nowrap">
                                       <div className="flex flex-col space-y-1">
                                          <span className="px-2 py-0.5 text-xs rounded-sm bg-gradient-to-r from-gray-900 to-gray-800 text-emerald-300 border border-gray-700">
                                             Time Range: {config.time_range_hours}h
                                          </span>
                                          <span className="px-2 py-0.5 text-xs rounded-sm bg-gradient-to-r from-gray-900 to-gray-800 text-blue-300 border border-gray-700">
                                             Limit: {config.limit_articles} articles
                                          </span>
                                          <span className="px-2 py-0.5 text-xs rounded-sm bg-gradient-to-r from-gray-900 to-gray-800 text-purple-300 border border-gray-700">
                                             TTS: {config.tts_engine || 'elevenlabs'} (
                                             {config.language_code || 'en'})
                                          </span>
                                       </div>
                                    </td>
                                    <td className="px-4 py-3 whitespace-nowrap">
                                       <div className="flex items-center">
                                          <ToggleSwitch
                                             enabled={config.is_active}
                                             onChange={() =>
                                                handleConfigToggle(config.id, config.is_active)
                                             }
                                          />
                                          <span
                                             className={`ml-2 text-sm ${
                                                config.is_active
                                                   ? 'text-emerald-400'
                                                   : 'text-gray-500'
                                             }`}
                                          >
                                             {config.is_active ? 'Active' : 'Inactive'}
                                          </span>
                                       </div>
                                    </td>
                                    <td className="px-4 py-3 whitespace-nowrap text-right text-sm font-medium">
                                       <div className="flex justify-end space-x-2">
                                          <button
                                             onClick={() => handleEditConfig(config)}
                                             className="text-gray-400 hover:text-blue-400 transition-colors duration-200"
                                             title="Edit"
                                          >
                                             <svg
                                                xmlns="http://www.w3.org/2000/svg"
                                                className="h-5 w-5"
                                                fill="none"
                                                viewBox="0 0 24 24"
                                                stroke="currentColor"
                                             >
                                                <path
                                                   strokeLinecap="round"
                                                   strokeLinejoin="round"
                                                   strokeWidth={2}
                                                   d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                                                />
                                             </svg>
                                          </button>
                                          <button
                                             onClick={() => handleConfigDelete(config.id)}
                                             className="text-gray-400 hover:text-red-400 transition-colors duration-200"
                                             title="Delete"
                                          >
                                             <svg
                                                xmlns="http://www.w3.org/2000/svg"
                                                className="h-5 w-5"
                                                fill="none"
                                                viewBox="0 0 24 24"
                                                stroke="currentColor"
                                             >
                                                <path
                                                   strokeLinecap="round"
                                                   strokeLinejoin="round"
                                                   strokeWidth={2}
                                                   d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                                                />
                                             </svg>
                                          </button>
                                       </div>
                                    </td>
                                 </tr>
                              ))}
                           </tbody>
                        </table>
                        {podcastConfigs.length === 0 && !loading && (
                           <div className="text-center py-8 text-gray-500">
                              No podcast configurations found
                           </div>
                        )}
                     </div>
                  )}
               </div>
            </div>
         )}
         {activeTab === 'executions' && (
            <div className="bg-gradient-to-br from-gray-800 to-gray-900 shadow-lg rounded-sm overflow-hidden border border-gray-700">
               <div className="h-0.5 w-full bg-gradient-to-r from-transparent via-emerald-800 to-transparent opacity-60"></div>
               <div className="p-4">
                  <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-4 space-y-2 sm:space-y-0">
                     <h3 className="text-lg font-medium text-gray-200">Task Executions</h3>
                     <div className="flex flex-wrap items-center space-x-2">
                        <div className="relative">
                           <select
                              value={selectedTaskId || ''}
                              onChange={e => {
                                 const value = e.target.value;
                                 handleFilterByTask(value ? parseInt(value) : null);
                              }}
                              className="bg-gradient-to-r from-gray-800 to-gray-900 border border-gray-700 text-gray-300 text-sm rounded-sm px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                           >
                              <option value="">All Tasks</option>
                              {tasks.map(task => (
                                 <option key={task.id} value={task.id}>
                                    {task.name}
                                 </option>
                              ))}
                           </select>
                           {selectedTaskId && (
                              <button
                                 onClick={handleClearTaskFilter}
                                 className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-500 hover:text-gray-300"
                                 title="Clear filter"
                              >
                                 <svg
                                    xmlns="http://www.w3.org/2000/svg"
                                    className="h-4 w-4"
                                    viewBox="0 0 20 20"
                                    fill="currentColor"
                                 >
                                    <path
                                       fillRule="evenodd"
                                       d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                                       clipRule="evenodd"
                                    />
                                 </svg>
                              </button>
                           )}
                        </div>
                        <button
                           onClick={() => loadTaskExecutions(selectedTaskId, executionsPage)}
                           className="px-3 py-1.5 text-sm rounded-sm bg-gradient-to-r from-gray-700 to-gray-800 text-gray-300 border border-gray-700 hover:border-gray-600 transition-colors duration-200"
                        >
                           Refresh
                        </button>
                     </div>
                  </div>
                  {loading ? (
                     <div className="flex justify-center py-20">
                        <div className="w-12 h-12 border-4 border-emerald-600 border-t-transparent rounded-full animate-spin"></div>
                     </div>
                  ) : (
                     <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-700">
                           <thead className="bg-gradient-to-r from-gray-900 to-gray-800">
                              <tr>
                                 <th
                                    scope="col"
                                    className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider"
                                 >
                                    Task
                                 </th>
                                 <th
                                    scope="col"
                                    className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider"
                                 >
                                    Status
                                 </th>
                                 <th
                                    scope="col"
                                    className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider"
                                 >
                                    Start Time
                                 </th>
                                 <th
                                    scope="col"
                                    className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider"
                                 >
                                    End Time
                                 </th>
                                 <th
                                    scope="col"
                                    className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider"
                                 >
                                    Output
                                 </th>
                              </tr>
                           </thead>
                           <tbody className="divide-y divide-gray-700">
                              {taskExecutions.map(execution => (
                                 <tr
                                    key={execution.id}
                                    className="hover:bg-gray-800 transition-all duration-200"
                                 >
                                    <td className="px-4 py-3 whitespace-nowrap">
                                       <div className="text-sm font-medium text-gray-200">
                                          {execution.task_name}
                                       </div>
                                       <div className="text-xs text-gray-500">
                                          ID: {execution.task_id}
                                       </div>
                                    </td>
                                    <td className="px-4 py-3 whitespace-nowrap">
                                       <span
                                          className={`flex items-center text-sm ${getStatusClass(
                                             execution.status
                                          )}`}
                                       >
                                          <span
                                             className={`h-2 w-2 rounded-full bg-current mr-2 ${
                                                execution.status === 'running'
                                                   ? 'animate-pulse'
                                                   : ''
                                             }`}
                                          ></span>
                                          {execution.status === 'success'
                                             ? 'Success'
                                             : execution.status === 'failed'
                                             ? 'Failed'
                                             : execution.status === 'running'
                                             ? 'Running'
                                             : execution.status}
                                       </span>
                                    </td>
                                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-400">
                                       {formatDate(execution.start_time)}
                                    </td>
                                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-400">
                                       {formatDate(execution.end_time)}
                                    </td>
                                    <td className="px-4 py-3 text-sm text-gray-400">
                                       <div className="flex items-center">
                                          <div className="font-mono bg-gray-900 p-2 rounded-sm text-xs truncate max-w-xs">
                                             {execution.output || 'No output'}
                                          </div>
                                          {execution.output && (
                                             <button
                                                onClick={() =>
                                                   handleViewOutput(
                                                      execution.output,
                                                      execution.task_name
                                                   )
                                                }
                                                className="ml-2 text-xs px-2 py-1 rounded-sm bg-gray-800 text-gray-300 hover:bg-gray-700 transition-colors"
                                             >
                                                View
                                             </button>
                                          )}
                                       </div>
                                    </td>
                                 </tr>
                              ))}
                           </tbody>
                        </table>
                        {taskExecutions.length === 0 && !loading && (
                           <div className="text-center py-8 text-gray-500">No executions found</div>
                        )}
                        {taskExecutions.length > 0 && (
                           <div className="mt-4 flex items-center justify-between">
                              <div className="text-sm text-gray-400">
                                 Showing{' '}
                                 <span className="font-medium text-gray-300">
                                    {taskExecutions.length}
                                 </span>{' '}
                                 of{' '}
                                 <span className="font-medium text-gray-300">
                                    {executionsTotal}
                                 </span>{' '}
                                 results
                              </div>

                              <div className="flex items-center space-x-2">
                                 <button
                                    onClick={() => handleExecutionsPageChange(1)}
                                    disabled={!executionsHasPrev}
                                    className={`relative inline-flex items-center px-2 py-1 rounded-sm text-sm font-medium ${
                                       executionsHasPrev
                                          ? 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                                          : 'bg-gray-800 text-gray-600 cursor-not-allowed'
                                    }`}
                                 >
                                    <span className="sr-only">First</span>
                                    <svg
                                       xmlns="http://www.w3.org/2000/svg"
                                       className="h-5 w-5"
                                       viewBox="0 0 20 20"
                                       fill="currentColor"
                                    >
                                       <path
                                          fillRule="evenodd"
                                          d="M15.707 15.707a1 1 0 01-1.414 0l-5-5a1 1 0 010-1.414l5-5a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 010 1.414zm-6 0a1 1 0 01-1.414 0l-5-5a1 1 0 010-1.414l5-5a1 1 0 011.414 1.414L5.414 10l4.293 4.293a1 1 0 010 1.414z"
                                          clipRule="evenodd"
                                       />
                                    </svg>
                                 </button>
                                 <button
                                    onClick={() => handleExecutionsPageChange(executionsPage - 1)}
                                    disabled={!executionsHasPrev}
                                    className={`relative inline-flex items-center px-2 py-1 rounded-sm text-sm font-medium ${
                                       executionsHasPrev
                                          ? 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                                          : 'bg-gray-800 text-gray-600 cursor-not-allowed'
                                    }`}
                                 >
                                    <span className="sr-only">Previous</span>
                                    <svg
                                       className="h-5 w-5"
                                       xmlns="http://www.w3.org/2000/svg"
                                       viewBox="0 0 20 20"
                                       fill="currentColor"
                                    >
                                       <path
                                          fillRule="evenodd"
                                          d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z"
                                          clipRule="evenodd"
                                       />
                                    </svg>
                                 </button>
                                 <span className="px-3 py-1 text-sm bg-gradient-to-b from-gray-700 to-gray-800 text-emerald-400 rounded-sm">
                                    {executionsPage} / {executionsTotalPages}
                                 </span>
                                 <button
                                    onClick={() => handleExecutionsPageChange(executionsPage + 1)}
                                    disabled={!executionsHasNext}
                                    className={`relative inline-flex items-center px-2 py-1 rounded-sm text-sm font-medium ${
                                       executionsHasNext
                                          ? 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                                          : 'bg-gray-800 text-gray-600 cursor-not-allowed'
                                    }`}
                                 >
                                    <span className="sr-only">Next</span>
                                    <svg
                                       className="h-5 w-5"
                                       xmlns="http://www.w3.org/2000/svg"
                                       viewBox="0 0 20 20"
                                       fill="currentColor"
                                    >
                                       <path
                                          fillRule="evenodd"
                                          d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
                                          clipRule="evenodd"
                                       />
                                    </svg>
                                 </button>
                                 <button
                                    onClick={() => handleExecutionsPageChange(executionsTotalPages)}
                                    disabled={!executionsHasNext}
                                    className={`relative inline-flex items-center px-2 py-1 rounded-sm text-sm font-medium ${
                                       executionsHasNext
                                          ? 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                                          : 'bg-gray-800 text-gray-600 cursor-not-allowed'
                                    }`}
                                 >
                                    <span className="sr-only">Last</span>
                                    <svg
                                       xmlns="http://www.w3.org/2000/svg"
                                       className="h-5 w-5"
                                       viewBox="0 0 20 20"
                                       fill="currentColor"
                                    >
                                       <path
                                          fillRule="evenodd"
                                          d="M10.293 15.707a1 1 0 010-1.414L14.586 10l-4.293-4.293a1 1 0 111.414-1.414l5 5a1 1 0 010 1.414l-5 5a1 1 0 01-1.414 0z"
                                          clipRule="evenodd"
                                       />
                                       <path
                                          fillRule="evenodd"
                                          d="M4.293 15.707a1 1 0 010-1.414L8.586 10 4.293 5.707a1 1 0 011.414-1.414l5 5a1 1 0 010 1.414l-5 5a1 1 0 01-1.414 0z"
                                          clipRule="evenodd"
                                       />
                                    </svg>
                                 </button>
                              </div>
                           </div>
                        )}
                     </div>
                  )}
               </div>
            </div>
         )}
         {isModalOpen && (
            <div
               className="fixed inset-0 z-50 overflow-y-auto"
               aria-labelledby="modal-title"
               role="dialog"
               aria-modal="true"
            >
               <div
                  className="fixed inset-0 bg-black bg-opacity-75 transition-opacity"
                  onClick={handleCloseModal}
               ></div>
               <div className="flex items-center justify-center min-h-screen p-4">
                  <div
                     className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-sm max-w-lg w-full p-6 shadow-2xl border border-gray-700 relative transform transition-all"
                     onClick={e => e.stopPropagation()}
                  >
                     <button
                        onClick={handleCloseModal}
                        className="absolute top-4 right-4 text-gray-400 hover:text-gray-200 transition-colors duration-200"
                        aria-label="Close"
                     >
                        <svg
                           xmlns="http://www.w3.org/2000/svg"
                           className="h-6 w-6"
                           fill="none"
                           viewBox="0 0 24 24"
                           stroke="currentColor"
                        >
                           <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M6 18L18 6M6 6l12 12"
                           />
                        </svg>
                     </button>
                     <h2 className="text-xl font-medium text-gray-200 mb-4">
                        {currentTask ? 'Edit Task' : 'Create New Task'}
                     </h2>
                     <TaskForm
                        task={currentTask}
                        onSubmit={handleTaskSubmit}
                        onCancel={handleCloseModal}
                     />
                     <div
                        className="absolute bottom-0 right-0 w-32 h-32 opacity-5"
                        style={{
                           backgroundImage:
                              'repeating-linear-gradient(45deg, #10B981 0, #10B981 1px, transparent 0, transparent 10px)',
                           clipPath: 'polygon(100% 0, 60% 0, 100% 40%)',
                        }}
                     ></div>
                  </div>
               </div>
            </div>
         )}
         {isConfigModalOpen && (
            <div
               className="fixed inset-0 z-50 overflow-y-auto"
               aria-labelledby="config-modal-title"
               role="dialog"
               aria-modal="true"
            >
               <div
                  className="fixed inset-0 bg-black bg-opacity-75 transition-opacity"
                  onClick={handleCloseConfigModal}
               ></div>
               <div className="flex items-center justify-center min-h-screen p-4">
                  <div
                     className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-sm max-w-2xl w-full p-6 shadow-2xl border border-gray-700 relative transform transition-all"
                     onClick={e => e.stopPropagation()}
                  >
                     <button
                        onClick={handleCloseConfigModal}
                        className="absolute top-4 right-4 text-gray-400 hover:text-gray-200 transition-colors duration-200"
                        aria-label="Close"
                     >
                        <svg
                           xmlns="http://www.w3.org/2000/svg"
                           className="h-6 w-6"
                           fill="none"
                           viewBox="0 0 24 24"
                           stroke="currentColor"
                        >
                           <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M6 18L18 6M6 6l12 12"
                           />
                        </svg>
                     </button>
                     <h2 className="text-xl font-medium text-gray-200 mb-4">
                        {currentConfig
                           ? 'Edit Podcast Configuration'
                           : 'Create New Podcast Configuration'}
                     </h2>
                     <PodcastConfigForm
                        config={currentConfig}
                        onSubmit={handleConfigSubmit}
                        onCancel={handleCloseConfigModal}
                     />
                     <div
                        className="absolute bottom-0 right-0 w-32 h-32 opacity-5"
                        style={{
                           backgroundImage:
                              'repeating-linear-gradient(45deg, #10B981 0, #10B981 1px, transparent 0, transparent 10px)',
                           clipPath: 'polygon(100% 0, 60% 0, 100% 40%)',
                        }}
                     ></div>
                  </div>
               </div>
            </div>
         )}
         {viewOutputModal && (
            <div
               className="fixed inset-0 z-50 overflow-y-auto"
               aria-labelledby="output-modal-title"
               role="dialog"
               aria-modal="true"
            >
               <div
                  className="fixed inset-0 bg-black bg-opacity-75 transition-opacity"
                  onClick={handleCloseOutputModal}
               ></div>
               <div className="flex items-center justify-center min-h-screen p-4">
                  <div
                     className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-sm max-w-3xl w-full p-6 shadow-2xl border border-gray-700 relative transform transition-all"
                     onClick={e => e.stopPropagation()}
                  >
                     <button
                        onClick={handleCloseOutputModal}
                        className="absolute top-4 right-4 text-gray-400 hover:text-gray-200 transition-colors duration-200"
                        aria-label="Close"
                     >
                        <svg
                           xmlns="http://www.w3.org/2000/svg"
                           className="h-6 w-6"
                           fill="none"
                           viewBox="0 0 24 24"
                           stroke="currentColor"
                        >
                           <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M6 18L18 6M6 6l12 12"
                           />
                        </svg>
                     </button>
                     <h2 className="text-xl font-medium text-gray-200 mb-4 pr-8">
                        Output: {currentOutputTaskName}
                     </h2>
                     <div className="bg-gray-900 p-4 rounded-sm text-xs font-mono text-gray-300 h-96 overflow-y-auto whitespace-pre-wrap">
                        {currentOutput}
                     </div>
                  </div>
               </div>
            </div>
         )}
      </div>
   );
};

export default Voyager;
