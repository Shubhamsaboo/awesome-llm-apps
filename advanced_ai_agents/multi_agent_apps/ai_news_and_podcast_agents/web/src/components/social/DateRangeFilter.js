import React, { useState, useEffect } from 'react';
import { Calendar, ChevronDown, RefreshCw } from 'lucide-react';

const DateRangeFilter = ({ onDateRangeChange, initialDateRange }) => {
   const presets = [
      { label: 'Last 7 days', days: 7 },
      { label: 'Last 30 days', days: 30 },
      { label: 'Last 90 days', days: 90 },
      { label: 'Year to date', value: 'ytd' },
      { label: 'Custom', value: 'custom' },
   ];
   const [selectedPreset, setSelectedPreset] = useState(presets[0]);
   const [isOpen, setIsOpen] = useState(false);
   const [customRange, setCustomRange] = useState({
      startDate: initialDateRange?.startDate || formatDateForInput(getDateBefore(7)),
      endDate: initialDateRange?.endDate || formatDateForInput(new Date()),
   });
   const [isCustom, setIsCustom] = useState(false);
   function getDateBefore(days) {
      const date = new Date();
      date.setDate(date.getDate() - days);
      return date;
   }
   function formatDateForInput(date) {
      return date.toISOString().split('T')[0];
   }
   function formatDateForDisplay(dateString) {
      const options = { month: 'short', day: 'numeric', year: 'numeric' };
      return new Date(dateString).toLocaleDateString(undefined, options);
   }
   function calculateDateRange(preset) {
      const endDate = new Date();
      let startDate;

      if (preset.days) {
         startDate = getDateBefore(preset.days);
      } else if (preset.value === 'ytd') {
         startDate = new Date(endDate.getFullYear(), 0, 1);
      } else if (preset.value === 'custom') {
         startDate = new Date(customRange.startDate);
         return { startDate, endDate: new Date(customRange.endDate) };
      }

      return {
         startDate,
         endDate,
      };
   }

   useEffect(() => {
      if (initialDateRange) {
         setCustomRange({
            startDate: initialDateRange.startDate,
            endDate: initialDateRange.endDate,
         });
         const start = new Date(initialDateRange.startDate);
         const end = new Date(initialDateRange.endDate);
         const daysDiff = Math.ceil((end - start) / (1000 * 60 * 60 * 24));
         let matchingPreset = presets.find(p => p.days === daysDiff);
         if (matchingPreset) {
            setSelectedPreset(matchingPreset);
            setIsCustom(false);
         } else {
            const yearStart = new Date(end.getFullYear(), 0, 1);
            if (start.getTime() === yearStart.getTime()) {
               setSelectedPreset(presets.find(p => p.value === 'ytd'));
               setIsCustom(false);
            } else {
               setSelectedPreset(presets.find(p => p.value === 'custom'));
               setIsCustom(true);
            }
         }
      }
   }, [initialDateRange]);

   const handlePresetSelect = preset => {
      setSelectedPreset(preset);
      setIsOpen(false);
      const { startDate, endDate } = calculateDateRange(preset);
      const formattedRange = {
         startDate: formatDateForInput(startDate),
         endDate: formatDateForInput(endDate),
      };
      setCustomRange(formattedRange);
      setIsCustom(preset.value === 'custom');
      onDateRangeChange(formattedRange);
   };
   const handleCustomDateChange = e => {
      const { name, value } = e.target;
      const newCustomRange = {
         ...customRange,
         [name]: value,
      };
      setCustomRange(newCustomRange);
      if (isCustom) {
         onDateRangeChange(newCustomRange);
      }
   };
   const applyCustomRange = () => {
      setIsCustom(true);
      setSelectedPreset(presets.find(p => p.value === 'custom'));
      setIsOpen(false);
      onDateRangeChange(customRange);
   };
   const handleRefresh = () => {
      if (isCustom) {
         onDateRangeChange(customRange);
      } else {
         const { startDate, endDate } = calculateDateRange(selectedPreset);
         const formattedRange = {
            startDate: formatDateForInput(startDate),
            endDate: formatDateForInput(endDate),
         };
         setCustomRange(formattedRange);
         onDateRangeChange(formattedRange);
      }
   };

   return (
      <div className="bg-gradient-to-br from-gray-800 to-gray-900 shadow-lg rounded-sm p-4 mb-6 border border-gray-700 relative">
         <div className="flex items-center justify-between">
            <div className="flex items-center">
               <Calendar className="h-5 w-5 text-emerald-500 mr-2" />
               <span className="text-sm font-medium text-gray-300">Date Range</span>
            </div>
            <div className="relative ml-4 flex-1">
               <button
                  onClick={() => setIsOpen(!isOpen)}
                  className="w-full sm:w-auto flex items-center justify-between bg-gradient-to-r from-gray-900 to-gray-800 hover:from-gray-800 hover:to-gray-700 text-gray-300 px-3 py-2 rounded-sm text-sm border border-gray-700 transition-colors"
               >
                  <span className="flex items-center">
                     {!isCustom ? selectedPreset.label : 'Custom Range'}
                     {isCustom && (
                        <span className="ml-2 text-xs text-gray-400">
                           ({formatDateForDisplay(customRange.startDate)} -{' '}
                           {formatDateForDisplay(customRange.endDate)})
                        </span>
                     )}
                  </span>
                  <ChevronDown className="h-4 w-4 ml-2" />
               </button>
               {isOpen && (
                  <div className="absolute top-full left-0 mt-1 z-10 bg-gray-800 border border-gray-700 rounded-sm shadow-lg w-full sm:w-80">
                     <div className="p-2">
                        <div className="space-y-1 mb-3">
                           {presets.map(preset => (
                              <button
                                 key={preset.label}
                                 onClick={() => handlePresetSelect(preset)}
                                 className={`w-full text-left px-3 py-2 rounded-sm text-sm ${
                                    selectedPreset.label === preset.label
                                       ? 'bg-emerald-700/30 text-emerald-300 border border-emerald-600/50'
                                       : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                                 } transition-colors`}
                              >
                                 {preset.label}
                              </button>
                           ))}
                        </div>
                        <div className="border-t border-gray-700 pt-3">
                           <div className="text-xs font-medium text-gray-400 mb-2">
                              Custom Range
                           </div>
                           <div className="grid grid-cols-2 gap-2">
                              <div>
                                 <label className="text-xs text-gray-500 block mb-1">
                                    Start Date
                                 </label>
                                 <input
                                    type="date"
                                    name="startDate"
                                    value={customRange.startDate}
                                    onChange={handleCustomDateChange}
                                    className="w-full bg-gray-900 border border-gray-700 rounded-sm px-2 py-1 text-xs text-gray-300 focus:outline-none focus:ring-1 focus:ring-emerald-500 focus:border-emerald-600"
                                 />
                              </div>
                              <div>
                                 <label className="text-xs text-gray-500 block mb-1">
                                    End Date
                                 </label>
                                 <input
                                    type="date"
                                    name="endDate"
                                    value={customRange.endDate}
                                    onChange={handleCustomDateChange}
                                    className="w-full bg-gray-900 border border-gray-700 rounded-sm px-2 py-1 text-xs text-gray-300 focus:outline-none focus:ring-1 focus:ring-emerald-500 focus:border-emerald-600"
                                 />
                              </div>
                           </div>
                           <button
                              onClick={applyCustomRange}
                              className="mt-3 w-full bg-emerald-700 hover:bg-emerald-600 text-emerald-100 py-1.5 px-3 rounded-sm text-xs font-medium transition-colors"
                           >
                              Apply Custom Range
                           </button>
                        </div>
                     </div>
                  </div>
               )}
            </div>

            <button
               className="ml-2 p-2 bg-gray-900 hover:bg-gray-800 rounded-sm border border-gray-700 text-gray-400 hover:text-emerald-400 transition-colors"
               title="Refresh data"
               onClick={handleRefresh}
            >
               <RefreshCw className="h-4 w-4" />
            </button>
         </div>
      </div>
   );
};

export default DateRangeFilter;
