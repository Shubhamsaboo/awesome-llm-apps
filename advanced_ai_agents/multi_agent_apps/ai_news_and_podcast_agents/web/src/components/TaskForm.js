import React, { useState, useEffect } from 'react';
import api from '../services/api';

const TaskForm = ({ task = null, onSubmit, onCancel }) => {
   const [name, setName] = useState('');
   const [description, setDescription] = useState('');
   const [taskType, setTaskType] = useState('');
   const [frequency, setFrequency] = useState(1);
   const [frequencyUnit, setFrequencyUnit] = useState('days');
   const [enabled, setEnabled] = useState(true);
   const [loading, setLoading] = useState(false);
   const [error, setError] = useState(null);
   const [taskTypes, setTaskTypes] = useState({});
   const [loadingTypes, setLoadingTypes] = useState(true);
   useEffect(() => {
      const fetchTaskTypes = async () => {
         setLoadingTypes(true);
         try {
            const response = await api.tasks.getTypes();
            setTaskTypes(response.data);
         } catch (err) {
            console.error('Error fetching task types:', err);
            setError('Failed to load task types. Please try again.');
         } finally {
            setLoadingTypes(false);
         }
      };

      fetchTaskTypes();
   }, []);

   useEffect(() => {
      if (task) {
         setName(task.name || '');
         setDescription(task.description || '');
         setTaskType(task.task_type || '');
         setFrequency(task.frequency || 1);
         setFrequencyUnit(task.frequency_unit || 'days');
         setEnabled(task.enabled !== undefined ? task.enabled : true);
      }
   }, [task]);

   const handleSubmit = async e => {
      e.preventDefault();
      setLoading(true);
      setError(null);
      try {
         if (!taskType) {
            throw new Error('Please select a task type');
         }
         const taskData = {
            name,
            description,
            task_type: taskType,
            frequency: parseInt(frequency),
            frequency_unit: frequencyUnit,
            enabled,
         };
         await onSubmit(taskData);
      } catch (err) {
         let errorMessage = 'Failed to save task';
         if (err.response && err.response.data) {
            if (err.response.data.detail) {
               errorMessage = err.response.data.detail;
            } else if (typeof err.response.data === 'string') {
               errorMessage = err.response.data;
            }
         } else if (err.message) {
            errorMessage = err.message;
         }

         setError(errorMessage);
      } finally {
         setLoading(false);
      }
   };

   return (
      <form onSubmit={handleSubmit} className="space-y-4">
         {error && (
            <div className="bg-gradient-to-r from-red-900 to-red-800 text-red-300 p-3 rounded-sm">
               {error}
            </div>
         )}
         <div>
            <label htmlFor="name" className="block text-sm font-medium text-gray-300 mb-1">
               Task Name <span className="text-red-400">*</span>
            </label>
            <input
               type="text"
               id="name"
               value={name}
               onChange={e => setName(e.target.value)}
               required
               className="w-full px-3 py-2 bg-gradient-to-r from-gray-900 to-gray-800 border border-gray-700 rounded-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-emerald-500 focus:border-emerald-400 sm:text-sm text-gray-300"
            />
         </div>
         <div>
            <label htmlFor="taskType" className="block text-sm font-medium text-gray-300 mb-1">
               Task Type <span className="text-red-400">*</span>
            </label>
            {loadingTypes ? (
               <div className="flex items-center space-x-2 text-gray-400 text-sm">
                  <div className="w-4 h-4 border-2 border-emerald-600 border-t-transparent rounded-full animate-spin"></div>
                  <span>Loading task types...</span>
               </div>
            ) : (
               <select
                  id="taskType"
                  value={taskType}
                  onChange={e => setTaskType(e.target.value)}
                  required
                  className="w-full px-3 py-2 bg-gradient-to-r from-gray-900 to-gray-800 border border-gray-700 rounded-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-emerald-500 focus:border-emerald-400 sm:text-sm text-gray-300"
               >
                  <option value="">-- Select a task type --</option>
                  {Object.entries(taskTypes).map(([key, type]) => (
                     <option key={key} value={key}>
                        {type.name}
                     </option>
                  ))}
               </select>
            )}
            {taskType && taskTypes[taskType] && (
               <p className="mt-1 text-xs text-gray-400">{taskTypes[taskType].description}</p>
            )}
            {taskType && taskTypes[taskType] && (
               <div className="mt-2 p-2 bg-gray-900 rounded-sm border border-gray-700">
                  <p className="text-xs text-gray-500 mb-1">Command (auto-generated):</p>
                  <code className="text-xs text-emerald-400 font-mono">
                     {taskTypes[taskType].command}
                  </code>
               </div>
            )}
         </div>
         <div>
            <label htmlFor="description" className="block text-sm font-medium text-gray-300 mb-1">
               Description
            </label>
            <textarea
               id="description"
               value={description}
               onChange={e => setDescription(e.target.value)}
               rows="2"
               className="w-full px-3 py-2 bg-gradient-to-r from-gray-900 to-gray-800 border border-gray-700 rounded-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-emerald-500 focus:border-emerald-400 sm:text-sm text-gray-300"
            />
         </div>
         <div className="grid grid-cols-2 gap-4">
            <div>
               <label htmlFor="frequency" className="block text-sm font-medium text-gray-300 mb-1">
                  Frequency <span className="text-red-400">*</span>
               </label>
               <input
                  type="number"
                  id="frequency"
                  value={frequency}
                  onChange={e => setFrequency(e.target.value)}
                  min="1"
                  required
                  className="w-full px-3 py-2 bg-gradient-to-r from-gray-900 to-gray-800 border border-gray-700 rounded-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-emerald-500 focus:border-emerald-400 sm:text-sm text-gray-300"
               />
            </div>
            <div>
               <label
                  htmlFor="frequencyUnit"
                  className="block text-sm font-medium text-gray-300 mb-1"
               >
                  Frequency Unit <span className="text-red-400">*</span>
               </label>
               <select
                  id="frequencyUnit"
                  value={frequencyUnit}
                  onChange={e => setFrequencyUnit(e.target.value)}
                  className="w-full px-3 py-2 bg-gradient-to-r from-gray-900 to-gray-800 border border-gray-700 rounded-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-emerald-500 focus:border-emerald-400 sm:text-sm text-gray-300"
               >
                  <option value="minutes">Minutes</option>
                  <option value="hours">Hours</option>
                  <option value="days">Days</option>
               </select>
            </div>
         </div>
         <div className="flex items-center">
            <input
               type="checkbox"
               id="enabled"
               checked={enabled}
               onChange={e => setEnabled(e.target.checked)}
               className="h-4 w-4 text-emerald-600 bg-gray-900 border-gray-700 rounded focus:ring-emerald-500 focus:ring-offset-gray-900"
            />
            <label htmlFor="enabled" className="ml-2 block text-sm text-gray-300">
               Enable task on creation
            </label>
         </div>
         <div className="flex justify-end space-x-3 pt-4">
            <button
               type="button"
               onClick={onCancel}
               className="px-4 py-2 bg-gradient-to-r from-gray-700 to-gray-800 hover:from-gray-600 hover:to-gray-700 text-gray-300 rounded-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 focus:ring-offset-gray-900 text-sm transition-colors duration-200"
            >
               Cancel
            </button>
            <button
               type="submit"
               disabled={loading || loadingTypes}
               className="px-4 py-2 bg-gradient-to-r from-emerald-700 to-emerald-800 hover:from-emerald-600 hover:to-emerald-700 text-white rounded-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 focus:ring-offset-gray-900 text-sm transition-colors duration-200 flex items-center disabled:opacity-50 disabled:cursor-not-allowed"
            >
               {loading && (
                  <svg
                     className="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
                     xmlns="http://www.w3.org/2000/svg"
                     fill="none"
                     viewBox="0 0 24 24"
                  >
                     <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                     ></circle>
                     <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                     ></path>
                  </svg>
               )}
               {task ? 'Update Task' : 'Create Task'}
            </button>
         </div>
      </form>
   );
};

export default TaskForm;
