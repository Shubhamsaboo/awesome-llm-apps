import React, { useState, useEffect } from 'react';

import api from '../services/api';

const PonyoChatIcon = ({ size = 40, isLoading = false, glowIntensity = 'ultra' }) => {
   const baseUrl = api?.API_BASE_URL || '';
   const imageUrl = `${baseUrl}/server_static/images/ponyo.png`;
   const [isHovered, setIsHovered] = useState(false);
   const [heartbeat, setHeartbeat] = useState(false);
   const [rayAngle, setRayAngle] = useState(0);

   useEffect(() => {
      if (isLoading) return;

      const heartbeatInterval = setInterval(() => {
         setHeartbeat(true);
         setTimeout(() => setHeartbeat(false), 300);
      }, 4000);

      return () => clearInterval(heartbeatInterval);
   }, [isLoading]);
   useEffect(() => {
      if (isLoading) return;

      const rayInterval = setInterval(() => {
         setRayAngle(prevAngle => (prevAngle + 0.5) % 360);
      }, 50);

      return () => clearInterval(rayInterval);
   }, [isLoading]);

   const glowValues = {
      low: { blur: 'blur-md', opacity: 'opacity-20', scale: 1.15 },
      medium: { blur: 'blur-lg', opacity: 'opacity-30', scale: 1.2 },
      high: { blur: 'blur-xl', opacity: 'opacity-40', scale: 1.25 },
      ultra: { blur: 'blur-xl', opacity: 'opacity-50', scale: 1.3 },
   };
   const glow = glowValues[glowIntensity] || glowValues.high;

   return (
      <div
         className="relative flex-shrink-0"
         style={{
            width: `${size}px`,
            height: `${size}px`,
         }}
         onMouseEnter={() => setIsHovered(true)}
         onMouseLeave={() => setIsHovered(false)}
      >
         <div
            className={`absolute inset-0 bg-blue-400 ${glow.opacity} rounded-full ${glow.blur} transition-all duration-300 ocean-outer-glow`}
            style={{
               transform: `scale(${heartbeat || isHovered ? glow.scale + 0.1 : glow.scale})`,
            }}
         ></div>
         <div
            className={`absolute inset-0 bg-sky-300 opacity-20 rounded-full blur-md transition-all duration-300`}
            style={{
               transform: `scale(${heartbeat || isHovered ? 1.15 : 1.1})`,
            }}
         ></div>
         <div className="absolute inset-0 overflow-hidden">
            {[...Array(8)].map((_, i) => (
               <div
                  key={i}
                  className="absolute top-1/2 left-1/2 h-full w-1 bg-gradient-to-t from-blue-400/0 via-cyan-300/40 to-blue-400/0 ocean-ray"
                  style={{
                     transformOrigin: 'bottom center',
                     transform: `translateX(-50%) rotate(${rayAngle + i * 45}deg) translateY(-25%)`,
                     opacity: isHovered ? 0.7 : 0.4,
                  }}
               ></div>
            ))}
         </div>
         <div className="absolute inset-0 rounded-full border border-gray-700 bg-gradient-to-br from-gray-800 via-gray-900 to-gray-800"></div>
         {!isLoading && (
            <>
               <div className="absolute inset-0 rounded-full border border-blue-400/30 ocean-ring-1"></div>
               <div className="absolute inset-0 rounded-full border border-blue-500/20 ocean-ring-2"></div>
               <div className="absolute inset-0 rounded-full border border-cyan-300/10 ocean-ring-3"></div>
            </>
         )}
         <div className="absolute inset-0 rounded-full bg-gray-900/60 overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-gray-800/10 via-transparent to-transparent"></div>
         </div>
         <div
            className={`absolute inset-0 rounded-full overflow-hidden transition-transform duration-300 ease-in-out ${
               isLoading ? '' : 'enhanced-float'
            }`}
            style={{
               transform: isHovered && !isLoading ? 'scale(1.05) translateY(-2px)' : 'scale(1)',
            }}
         >
            <div
               className="absolute inset-0 rounded-full bg-blue-500/5 ocean-inner-glow"
               style={{
                  filter: `blur(${isHovered ? 5 : 2}px)`,
                  opacity: heartbeat ? 0.4 : isHovered ? 0.35 : 0.25,
                  transition: 'filter 0.3s ease, opacity 0.3s ease',
               }}
            ></div>
            <div className="absolute top-1/4 left-1/4 w-1/6 h-1/6 rounded-full bg-sky-300/40 blur-sm"></div>
            <div className="absolute bottom-1/5 right-1/4 w-1/10 h-1/10 rounded-full bg-cyan-200/30 blur-sm ocean-spot-pulse"></div>
            <div className="absolute top-0 left-0 w-1/3 h-1/3 rounded-full bg-white/10 transform translate-x-1/4 translate-y-1/4"></div>
            <div className="absolute bottom-1/4 right-1/4 w-1/5 h-1/5 rounded-full bg-white/5"></div>
            <div
               className="w-full h-full bg-contain bg-center bg-no-repeat transition-transform duration-300"
               style={{
                  backgroundImage: `url('${imageUrl}')`,
                  backgroundColor: 'transparent',
                  transform: isHovered && !isLoading ? 'scale(1.05)' : 'scale(1)',
               }}
            ></div>
         </div>
         {isLoading && (
            <>
               <div
                  className="absolute inset-0 rounded-full border-2 border-blue-400/70 border-t-transparent animate-spin"
                  style={{ animationDuration: '1.5s' }}
               ></div>
               <div
                  className="absolute inset-0 rounded-full border border-cyan-300/40 border-b-transparent animate-spin"
                  style={{ animationDuration: '2.5s', padding: '3px' }}
               ></div>
               <div className="absolute inset-0 flex items-center justify-center">
                  <div className="w-1/4 h-1/4 bg-blue-400/80 rounded-full animate-ping ocean-ping"></div>
               </div>
               <div className="absolute inset-0 rounded-full bg-blue-500/10 blur-md animate-pulse"></div>
            </>
         )}
         <style jsx>{`
            @keyframes enhanced-float {
               0%,
               100% {
                  transform: translateY(0) rotate(0);
               }
               25% {
                  transform: translateY(-3px) rotate(0.5deg);
               }
               50% {
                  transform: translateY(-5px) rotate(0);
               }
               75% {
                  transform: translateY(-2px) rotate(-0.5deg);
               }
            }

            @keyframes ocean-inner-glow {
               0%,
               100% {
                  opacity: 0.25;
                  transform: scale(0.98);
               }
               50% {
                  opacity: 0.4;
                  transform: scale(1.05);
               }
            }

            @keyframes ocean-outer-glow {
               0%,
               100% {
                  opacity: 0.3;
                  filter: blur(8px);
               }
               50% {
                  opacity: 0.5;
                  filter: blur(12px);
               }
            }

            @keyframes ocean-ring-1 {
               0% {
                  transform: scale(0.95);
                  opacity: 0.5;
               }
               100% {
                  transform: scale(1.25);
                  opacity: 0;
               }
            }

            @keyframes ocean-ring-2 {
               0% {
                  transform: scale(0.9);
                  opacity: 0.4;
               }
               100% {
                  transform: scale(1.3);
                  opacity: 0;
               }
            }

            @keyframes ocean-ring-3 {
               0% {
                  transform: scale(1);
                  opacity: 0.3;
               }
               100% {
                  transform: scale(1.4);
                  opacity: 0;
               }
            }

            @keyframes ocean-ray {
               0% {
                  opacity: 0.1;
                  height: 100%;
               }
               50% {
                  opacity: 0.4;
                  height: 120%;
               }
               100% {
                  opacity: 0.1;
                  height: 100%;
               }
            }

            @keyframes ocean-spot-pulse {
               0%,
               100% {
                  opacity: 0.2;
                  transform: scale(1);
               }
               50% {
                  opacity: 0.5;
                  transform: scale(1.5);
               }
            }

            @keyframes ocean-ping {
               0% {
                  transform: scale(0.8);
                  opacity: 0.8;
               }
               75%,
               100% {
                  transform: scale(1.5);
                  opacity: 0;
               }
            }

            .enhanced-float {
               animation: enhanced-float 4s ease-in-out infinite;
            }

            .ocean-inner-glow {
               animation: ocean-inner-glow 5s ease-in-out infinite;
            }

            .ocean-outer-glow {
               animation: ocean-outer-glow 6s ease-in-out infinite;
            }

            .ocean-ring-1 {
               animation: ocean-ring-1 3s ease-out infinite;
            }

            .ocean-ring-2 {
               animation: ocean-ring-2 3.5s ease-out infinite;
               animation-delay: 0.5s;
            }

            .ocean-ring-3 {
               animation: ocean-ring-3 4s ease-out infinite;
               animation-delay: 1s;
            }

            .ocean-ray {
               animation: ocean-ray 3s ease-in-out infinite;
               animation-delay: calc(var(--index) * 0.5s);
            }

            .ocean-spot-pulse {
               animation: ocean-spot-pulse 4s ease-in-out infinite;
            }

            .ocean-ping {
               animation: ocean-ping 2s cubic-bezier(0, 0, 0.2, 1) infinite;
            }
         `}</style>
      </div>
   );
};

const ChatMessage = ({ message, role }) => {
   const formatMarkdown = content => {
      try {
         return content
            .replace(/\*\*(.*?)\*\*/g, '<strong class="text-white">$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\n/g, '<br>')
            .replace(
               /!\[(.*?)\]\((.*?)\)/g,
               '<img src="$2" alt="$1" class="max-w-full rounded-sm my-2 border border-gray-700">'
            )
            .replace(
               /• (.*?)(?:<br>|$)/g,
               '<div class="flex mt-1"><span class="mr-2 text-emerald-400">•</span><span>$1</span></div>'
            );
      } catch (error) {
         console.error('Error formatting message:', error);
         return content;
      }
   };
   return role === 'user' ? (
      <div className="mb-4 flex justify-end fade-in">
         <div className="max-w-[80%] bg-gradient-to-r from-emerald-700 to-emerald-800 text-white px-4 py-3 rounded-md rounded-tr-none text-sm shadow-md">
            {message}
         </div>
      </div>
   ) : (
      <div className="mb-4 flex fade-in">
         <div className="w-10 h-10 rounded-full relative flex-shrink-0 mr-3 mt-1">
            <PonyoChatIcon size={40} />
         </div>
         <div
            className="max-w-[80%] bg-gradient-to-r from-gray-800 to-gray-900 text-gray-200 px-4 py-3 rounded-md rounded-tl-none text-sm shadow-md"
            dangerouslySetInnerHTML={{ __html: formatMarkdown(message) }}
         />
      </div>
   );
};

export const LoadingIndicator = () => {
   const message = 'The agent is working. Please wait this may take a while...';
   return (
      <div className="my-2">
         <div className="bg-gray-900/60 backdrop-blur-md rounded-lg p-3 flex items-center relative overflow-hidden border border-white/10 shadow-lg">
            <div className="absolute inset-0">
               <div className="absolute top-0 left-0 w-full h-16 bg-gradient-to-b from-emerald-500/10 to-transparent"></div>
               <div className="absolute -inset-1 bg-grid-pattern opacity-5"></div>
            </div>
            <div className="relative z-10 mr-3">
               <div className="relative">
                  <PonyoChatIcon size={32} isLoading={true} />
                  <div className="absolute inset-0 rounded-full border-2 border-emerald-500/20 border-t-emerald-400 animate-spin-slow"></div>
                  <div className="absolute -inset-1 bg-emerald-400/10 rounded-full blur-sm animate-pulse-glow"></div>
               </div>
            </div>
            <div className="flex-1 flex flex-col z-10">
               <div className="flex justify-between items-center mb-2">
                  <span className="text-sm text-gray-100 font-medium">{message}</span>
                  <div className="flex space-x-1">
                     {[...Array(3)].map((_, i) => (
                        <div
                           key={i}
                           className="w-1 h-1 rounded-full bg-emerald-400"
                           style={{
                              animation: `fadeInOut 1.2s ${i * 0.2}s infinite ease-in-out`,
                           }}
                        ></div>
                     ))}
                  </div>
               </div>
               <div className="h-1 w-full bg-gray-800/40 backdrop-blur-sm rounded-full overflow-hidden">
                  <div className="h-full rounded-full bg-gradient-to-r from-emerald-400/80 to-emerald-300/80 animate-loading-bar">
                     <div className="absolute inset-0 bg-white/20 rounded-full"></div>
                  </div>
               </div>
            </div>
         </div>
         <style jsx>{`
            .bg-grid-pattern {
               background-image: radial-gradient(
                  circle,
                  rgba(16, 185, 129, 0.2) 1px,
                  transparent 1px
               );
               background-size: 20px 20px;
            }

            @keyframes spin-slow {
               from {
                  transform: rotate(0deg);
               }
               to {
                  transform: rotate(360deg);
               }
            }

            @keyframes fadeInOut {
               0%,
               100% {
                  opacity: 0.2;
                  transform: scale(0.8);
               }
               50% {
                  opacity: 1;
                  transform: scale(1);
               }
            }

            @keyframes loading-bar {
               0% {
                  width: 10%;
               }
               20% {
                  width: 40%;
               }
               50% {
                  width: 60%;
               }
               80% {
                  width: 80%;
               }
               95% {
                  width: 90%;
               }
               100% {
                  width: 10%;
               }
            }

            @keyframes pulse-glow {
               0%,
               100% {
                  opacity: 0.1;
               }
               50% {
                  opacity: 0.3;
               }
            }

            .animate-spin-slow {
               animation: spin-slow 2s linear infinite;
            }

            .animate-loading-bar {
               animation: loading-bar 2.5s infinite;
            }

            .animate-pulse-glow {
               animation: pulse-glow 2s ease-in-out infinite;
            }
         `}</style>
      </div>
   );
};

export default ChatMessage;
