import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import { CheckCircle, AlertCircle, Clock, Shield, Globe, Zap, ArrowRight, Key } from 'lucide-react';

const SessionSetupTab = () => {
   const [isLoading, setIsLoading] = useState(false);
   const [message, setMessage] = useState('');
   const [messageType, setMessageType] = useState('');
   const [cooldownTime, setCooldownTime] = useState(0);
   const defaultSites = ['https://x.com', 'https://facebook.com'];

   useEffect(() => {
      let interval;
      if (cooldownTime > 0) {
         interval = setInterval(() => {
            setCooldownTime(prev => prev - 1);
         }, 1000);
      }
      return () => clearInterval(interval);
   }, [cooldownTime]);

   const handleSetupSession = async () => {
      if (cooldownTime > 0) return;
      setIsLoading(true);
      setMessage('');
      try {
         const response = await api.socialMedia.setupSession(defaultSites);
         if (response.data.status === 'ok') {
            setMessage(
               'Login session setup started! Browser will open for you to log into X.com and Facebook. Your login sessions will be saved for future monitoring.'
            );
            setMessageType('success');
            setCooldownTime(30);
         } else {
            setMessage('Failed to start login session setup. Please try again.');
            setMessageType('error');
         }
      } catch (error) {
         console.error('Session setup error:', error);
         setMessage(
            error.response?.data?.detail || 'Failed to start login session setup. Please try again.'
         );
         setMessageType('error');
      } finally {
         setIsLoading(false);
      }
   };
   const getMessageIcon = () => {
      switch (messageType) {
         case 'success':
            return <CheckCircle className="w-4 h-4 text-green-500" />;
         case 'error':
            return <AlertCircle className="w-4 h-4 text-red-500" />;
         default:
            return null;
      }
   };
   const getMessageBgColor = () => {
      switch (messageType) {
         case 'success':
            return 'bg-green-900/20 border-green-500/30 text-green-300';
         case 'error':
            return 'bg-red-900/20 border-red-500/30 text-red-300';
         default:
            return '';
      }
   };

   return (
      <div className="max-w-3xl mx-auto">
         <div className="relative overflow-hidden bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 border border-gray-700/50 rounded-xl shadow-2xl">
            <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-emerald-400/5 to-blue-400/5 rounded-full blur-xl transform translate-x-16 -translate-y-16"></div>
            <div className="absolute bottom-0 left-0 w-24 h-24 bg-gradient-to-tr from-emerald-400/3 to-purple-400/3 rounded-full blur-lg transform -translate-x-12 translate-y-12"></div>
            <div className="relative p-8">
               <div className="flex items-start space-x-4 mb-6">
                  <div className="relative">
                     <div className="absolute inset-0 bg-gradient-to-r from-emerald-400 to-blue-400 rounded-xl blur-md opacity-15"></div>
                     <div className="relative bg-gradient-to-r from-emerald-500/15 to-blue-500/15 p-3 rounded-xl border border-emerald-400/20">
                        <Key className="w-7 h-7 text-emerald-400" />
                     </div>
                  </div>
                  <div className="flex-1">
                     <h2 className="text-xl font-semibold text-gray-100 mb-1">
                        Login Session Setup
                     </h2>
                     <p className="text-gray-400 text-sm leading-relaxed">
                        One-time login to create authenticated sessions for monitoring
                     </p>
                  </div>
               </div>
               <div className="flex items-center space-x-4 mb-6 p-4 bg-gray-800/50 rounded-lg border border-gray-700/50">
                  <div className="flex items-center space-x-2">
                     <Shield className="w-4 h-4 text-emerald-400" />
                     <span className="text-sm text-gray-300 font-medium">Platforms:</span>
                  </div>
                  <div className="flex items-center space-x-3">
                     <div className="flex items-center space-x-2 px-3 py-1 bg-gray-700/50 rounded-md border border-gray-600/50">
                        <Globe className="w-3 h-3 text-blue-400" />
                        <span className="text-xs text-gray-300">X.com</span>
                     </div>
                     <div className="flex items-center space-x-2 px-3 py-1 bg-gray-700/50 rounded-md border border-gray-600/50">
                        <Globe className="w-3 h-3 text-blue-400" />
                        <span className="text-xs text-gray-300">Facebook</span>
                     </div>
                  </div>
               </div>
               <div className="space-y-4">
                  <button
                     onClick={handleSetupSession}
                     disabled={isLoading || cooldownTime > 0}
                     className={`group relative w-full py-4 px-6 rounded-xl font-medium transition-all duration-300 transform ${
                        isLoading || cooldownTime > 0
                           ? 'bg-gray-700/50 text-gray-400 cursor-not-allowed scale-100'
                           : 'bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-500 hover:to-emerald-400 text-white shadow-lg hover:shadow-emerald-500/15 hover:scale-105 active:scale-95'
                     }`}
                  >
                     {!(isLoading || cooldownTime > 0) && (
                        <div className="absolute inset-0 bg-gradient-to-r from-emerald-600 to-emerald-500 rounded-xl blur-xl opacity-15 group-hover:opacity-25 transition-opacity duration-300"></div>
                     )}
                     <div className="relative flex items-center justify-center space-x-3">
                        {isLoading ? (
                           <>
                              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                              <span>Starting login session setup...</span>
                           </>
                        ) : cooldownTime > 0 ? (
                           <>
                              <Clock className="w-5 h-5" />
                              <span>Browser opened - go login now (retry only if fails)</span>
                           </>
                        ) : (
                           <>
                              <Key className="w-5 h-5" />
                              <span>Create Login Sessions</span>
                              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform duration-200" />
                           </>
                        )}
                     </div>
                  </button>
                  {message && (
                     <div
                        className={`relative p-4 rounded-xl border backdrop-blur-sm ${getMessageBgColor()}`}
                     >
                        <div className="flex items-start space-x-3">
                           {getMessageIcon()}
                           <p className="text-sm leading-relaxed flex-1">{message}</p>
                        </div>
                     </div>
                  )}
                  <div className="bg-gray-800/30 rounded-lg p-4 border border-gray-700/30">
                     <div className="space-y-2">
                        <div className="flex items-center space-x-2">
                           <Zap className="w-4 h-4 text-amber-400" />
                           <span className="text-xs font-medium text-gray-300">When to use:</span>
                           <span className="text-xs text-gray-400">
                              Only if monitoring fails due to expired login sessions
                           </span>
                        </div>
                        <div className="flex items-center space-x-2">
                           <ArrowRight className="w-4 h-4 text-emerald-400" />
                           <span className="text-xs font-medium text-gray-300">Process:</span>
                           <span className="text-xs text-gray-400">
                              Browser opens → Login to X.com & Facebook → Sessions saved
                              automatically
                           </span>
                        </div>
                     </div>
                  </div>
               </div>
            </div>
         </div>
      </div>
   );
};

export default SessionSetupTab;
