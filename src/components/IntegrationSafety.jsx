import React from 'react';
import { Link, Shield, CheckCircle2 } from 'lucide-react';

export default function IntegrationSafety() {
  return (
    <section className="relative overflow-hidden py-16 sm:py-20 lg:py-24 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto w-full border-t border-slate-200/60 dark:border-slate-800/40">
      
      {/* TWO-COLUMN GRID */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 max-w-5xl mx-auto items-stretch">
        
        {/* CARD 1: Deep Integration */}
        <div className="bg-white dark:bg-[#0d1326]/60 border border-slate-100 dark:border-slate-800 shadow-xl shadow-slate-200/40 dark:shadow-black/25 rounded-3xl p-8 flex flex-col justify-between gap-6 transition-all duration-300 hover:border-slate-200 dark:hover:border-slate-700 hover:shadow-2xl hover:scale-[1.005]">
          
          <div className="space-y-4">
            <div className="w-10 h-10 rounded-xl bg-brand-50 dark:bg-brand-950/40 text-brand-650 dark:text-brand-400 flex items-center justify-center border border-brand-100/50 dark:border-brand-900/30 transition-all duration-300 flex-shrink-0">
              <Link size={18} />
            </div>

            <div className="space-y-2 text-left">
              <h3 className="text-xl sm:text-2xl font-bold text-slate-850 dark:text-white transition-colors duration-300">
                Deep Integration
              </h3>
              <p className="text-slate-500 dark:text-slate-400 text-sm leading-relaxed transition-colors duration-300">
                AetherLearn doesn't replace your stack; it supercharges it. Seamlessly connect with your existing infrastructure.
              </p>
            </div>
          </div>

          {/* Integration Bullets */}
          <div className="flex flex-col gap-3 text-left w-full">
            {/* Item 1 */}
            <div className="flex items-center gap-3 bg-slate-50 dark:bg-slate-900/40 border border-slate-100 dark:border-slate-800/80 rounded-2xl p-4 transition-colors duration-300">
              <CheckCircle2 size={16} className="text-brand-600 dark:text-brand-400 flex-shrink-0" />
              <span className="text-xs sm:text-sm font-semibold text-slate-700 dark:text-slate-200">
                Canvas, Blackboard & Moodle Sync
              </span>
            </div>

            {/* Item 2 */}
            <div className="flex items-center gap-3 bg-slate-50 dark:bg-slate-900/40 border border-slate-100 dark:border-slate-800/80 rounded-2xl p-4 transition-colors duration-300">
              <CheckCircle2 size={16} className="text-brand-600 dark:text-brand-400 flex-shrink-0" />
              <span className="text-xs sm:text-sm font-semibold text-slate-700 dark:text-slate-200">
                SSO / Active Directory Authentication
              </span>
            </div>

            {/* Item 3 */}
            <div className="flex items-center gap-3 bg-slate-50 dark:bg-slate-900/40 border border-slate-100 dark:border-slate-800/80 rounded-2xl p-4 transition-colors duration-300">
              <CheckCircle2 size={16} className="text-brand-600 dark:text-brand-400 flex-shrink-0" />
              <span className="text-xs sm:text-sm font-semibold text-slate-700 dark:text-slate-200">
                Custom API for Data Lakes
              </span>
            </div>
          </div>

        </div>

        {/* CARD 2: Safety & Ethics First */}
        <div className="bg-white dark:bg-[#0d1326]/60 border border-slate-100 dark:border-slate-800 shadow-xl shadow-slate-200/40 dark:shadow-black/25 rounded-3xl p-8 flex flex-col justify-between gap-6 transition-all duration-300 hover:border-slate-200 dark:hover:border-slate-700 hover:shadow-2xl hover:scale-[1.005]">
          
          <div className="space-y-4">
            <div className="w-10 h-10 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 text-emerald-650 dark:text-emerald-400 flex items-center justify-center border border-emerald-100/50 dark:border-emerald-900/30 transition-all duration-300 flex-shrink-0">
              <Shield size={18} />
            </div>

            <div className="space-y-2 text-left">
              <h3 className="text-xl sm:text-2xl font-bold text-slate-850 dark:text-white transition-colors duration-300">
                Safety & Ethics First
              </h3>
              <p className="text-slate-500 dark:text-slate-400 text-sm leading-relaxed transition-colors duration-300">
                Advanced AI requires advanced responsibility. Our models are built on transparency, privacy, and active bias mitigation.
              </p>
            </div>
          </div>

          {/* Metric Sub-cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-left w-full">
            
            {/* Block 1 */}
            <div className="bg-slate-50 dark:bg-slate-900/40 border border-slate-100 dark:border-slate-800/80 rounded-2xl p-5 flex flex-col gap-2 transition-colors duration-300">
              <span className="text-sm font-bold text-emerald-600 dark:text-emerald-400">
                Zero-Data Retention
              </span>
              <p className="text-xs leading-relaxed text-slate-500 dark:text-slate-400 transition-colors duration-300">
                Personal models are encrypted locally; training data is anonymized immediately.
              </p>
            </div>

            {/* Block 2 */}
            <div className="bg-slate-50 dark:bg-slate-900/40 border border-slate-100 dark:border-slate-800/80 rounded-2xl p-5 flex flex-col gap-2 transition-colors duration-300">
              <span className="text-sm font-bold text-emerald-600 dark:text-emerald-400">
                Algorithmic Audits
              </span>
              <p className="text-xs leading-relaxed text-slate-500 dark:text-slate-400 transition-colors duration-300">
                Quarterly third-party audits ensure recommendation models remain unbiased and fair.
              </p>
            </div>

          </div>

        </div>

      </div>
    </section>
  );
}
