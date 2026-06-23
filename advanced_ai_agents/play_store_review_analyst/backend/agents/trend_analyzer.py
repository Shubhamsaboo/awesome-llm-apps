import json
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
from backend.llm.llm_provider import LLMProvider

logger = logging.getLogger(__name__)


class TrendAnalyzer:
    """Agent that analyzes trends in classified reviews"""
    
    def __init__(self, llm_provider: LLMProvider, prompt_template: str):
        self.llm = llm_provider
        self.prompt_template = prompt_template
    
    def analyze_trends(self, reviews: List[Dict[str, Any]], 
                      topic_to_reviews: Dict[str, List[str]],
                      review_to_topics: Dict[str, Dict[str, Any]],
                      target_date: str = None, window_days: int = 30) -> Dict[str, Any]:
        """
        Analyze trends from reviews using topics.
        
        Args:
            reviews: List of all reviews
            topic_to_reviews: Mapping of topic names to review IDs
            review_to_topics: Mapping of review IDs to topic info
            target_date: Target date (YYYY-MM-DD), defaults to today
            window_days: Number of days to look back
            
        Returns:
            Dict with trend analysis results
        """
        try:
            if not target_date:
                target_date = datetime.now().strftime("%Y-%m-%d")
            
            # Build frequency table using topics
            freq_table = self._build_frequency_table(
                reviews, 
                topic_to_reviews,
                target_date,
                window_days
            )
            # Generate insights
            insights = self._generate_insights(freq_table)
            
            # ADD THESE NEW CALLS:
            severity_scores = self._calculate_severity_scores(reviews, topic_to_reviews, review_to_topics)
            peak_days = self._identify_peak_days(freq_table)
            weekly_trends = self._calculate_weekly_averages(freq_table)
            actionable_items = self._generate_actionable_recommendations(
                freq_table, severity_scores, insights, review_to_topics
            )
            
            # Then update the return statement:
            return {
                "frequency_table": freq_table,
                "insights": insights,
                "severity_scores": severity_scores,  # NEW
                "peak_days": peak_days,  # NEW
                "weekly_trends": weekly_trends,  # NEW
                "actionable_recommendations": actionable_items,  # NEW
                "target_date": target_date,
                "window_days": window_days,
            }
            
        except Exception as e:
            logger.error(f"Error analyzing trends: {str(e)}")
            raise
    
    def _build_frequency_table(self, reviews: List[Dict[str, Any]],
                              topic_to_reviews: Dict[str, List[str]],
                              target_date: str, window_days: int) -> Dict[str, Dict[str, int]]:
        """Build frequency table of topics by date"""
        try:
            target_dt = datetime.strptime(target_date, "%Y-%m-%d")
            start_dt = target_dt - timedelta(days=window_days)
            
            # Create review ID to review mapping for quick lookup
            review_map = {r.get("reviewId", ""): r for r in reviews}
            
            # Initialize frequency table for all topics
            freq_table = {}
            for topic in topic_to_reviews.keys():
                freq_table[topic] = {}
                
                # Initialize all dates with 0
                current_dt = start_dt
                while current_dt <= target_dt:
                    date_str = current_dt.strftime("%Y-%m-%d")
                    freq_table[topic][date_str] = 0
                    current_dt += timedelta(days=1)
            
            # Fill in frequencies by counting reviews per topic per date
            for topic, review_ids in topic_to_reviews.items():
                for review_id in review_ids:
                    review = review_map.get(review_id)
                    if not review:
                        continue
                    
                    # Extract date from review
                    review_date_str = review.get("at", "")
                    if isinstance(review_date_str, str):
                        review_date_str = review_date_str[:10]  # Extract YYYY-MM-DD
                    else:
                        continue
                    
                    try:
                        review_dt = datetime.strptime(review_date_str, "%Y-%m-%d")
                        if start_dt <= review_dt <= target_dt:
                            if review_date_str in freq_table[topic]:
                                freq_table[topic][review_date_str] += 1
                    except Exception as e:
                        logger.warning(f"Error parsing review date {review_date_str}: {str(e)}")
            
            logger.info(f"Built frequency table with {len(freq_table)} topics")
            return freq_table
            
        except Exception as e:
            logger.error(f"Error building frequency table: {str(e)}")
            return {}
    
    def _generate_insights(self, freq_table: Dict[str, Dict[str, int]]) -> Dict[str, Any]:
        """Generate trend insights"""
        try:
            # Find most frequent topics
            topic_totals = {}
            for topic, dates in freq_table.items():
                topic_totals[topic] = sum(dates.values())
            
            sorted_topics = sorted(topic_totals.items(), key=lambda x: x[1], reverse=True)
            
            top_topics = [topic for topic, _ in sorted_topics[:5]]
            
            # Find trending up/down
            trending_up = []
            trending_down = []
            
            if freq_table:
                dates = sorted(list(next(iter(freq_table.values())).keys()))
                if len(dates) > 1:
                    mid_point = len(dates) // 2
                    first_half_dates = dates[:mid_point]
                    second_half_dates = dates[mid_point:]
                    
                    for topic, date_freq in freq_table.items():
                        first_half_total = sum(date_freq[d] for d in first_half_dates if d in date_freq)
                        second_half_total = sum(date_freq[d] for d in second_half_dates if d in date_freq)
                        
                        if first_half_total > 0:
                            ratio = second_half_total / first_half_total
                            if ratio > 1.5:
                                trending_up.append((topic, ratio))
                            elif ratio < 0.7:
                                trending_down.append((topic, ratio))
                
                trending_up = sorted(trending_up, key=lambda x: x[1], reverse=True)[:3]
                trending_down = sorted(trending_down, key=lambda x: x[1])[:3]
            
            return {
                "top_topics": top_topics,
                "trending_up": [topic for topic, _ in trending_up],
                "trending_down": [topic for topic, _ in trending_down],
                "total_topics": len(freq_table),
            }
            
        except Exception as e:
            logger.error(f"Error generating insights: {str(e)}")
            return {}

    def _calculate_severity_scores(self, reviews: List[Dict[str, Any]],
                               topic_to_reviews: Dict[str, List[str]],
                               review_to_topics: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Calculate severity score for each topic based on ratings and frequency"""
        try:
            severity_scores = {}
            review_map = {r.get("reviewId", ""): r for r in reviews}
            
            for topic, review_ids in topic_to_reviews.items():
                ratings = []
                total_count = len(review_ids)
                
                for review_id in review_ids:
                    review = review_map.get(review_id)
                    if review:
                        rating = review.get("score", 3)
                        ratings.append(rating)
                
                if ratings:
                    avg_rating = sum(ratings) / len(ratings)
                    low_rating_count = sum(1 for r in ratings if r <= 2)
                    low_rating_pct = (low_rating_count / len(ratings)) * 100
                    
                    # Severity formula: lower rating + higher frequency = higher severity
                    # Scale: 0-100 (higher is more severe)
                    severity = ((5 - avg_rating) / 4) * 50 + (low_rating_pct * 0.5)
                    
                    severity_scores[topic] = {
                        "score": round(severity, 1),
                        "avg_rating": round(avg_rating, 2),
                        "total_reviews": total_count,
                        "low_rating_count": low_rating_count,
                        "low_rating_percentage": round(low_rating_pct, 1),
                        "classification": self._classify_severity(severity)
                    }
            
            logger.info(f"Calculated severity scores for {len(severity_scores)} topics")
            return severity_scores
            
        except Exception as e:
            logger.error(f"Error calculating severity scores: {str(e)}")
            return {}

    def _classify_severity(self, score: float) -> str:
        """Classify severity into categories"""
        if score >= 70:
            return "CRITICAL"
        elif score >= 50:
            return "HIGH"
        elif score >= 30:
            return "MEDIUM"
        else:
            return "LOW"

    def _identify_peak_days(self, freq_table: Dict[str, Dict[str, int]]) -> Dict[str, Dict[str, Any]]:
        """Identify peak days for each topic"""
        try:
            peak_days = {}
            
            for topic, date_freq in freq_table.items():
                if not date_freq:
                    continue
                
                max_count = max(date_freq.values())
                peak_dates = [date for date, count in date_freq.items() if count == max_count]
                
                peak_days[topic] = {
                    "peak_count": max_count,
                    "peak_dates": peak_dates,
                    "first_peak_date": peak_dates[0] if peak_dates else None
                }
            
            return peak_days
            
        except Exception as e:
            logger.error(f"Error identifying peak days: {str(e)}")
            return {}

    def _calculate_weekly_averages(self, freq_table: Dict[str, Dict[str, int]]) -> Dict[str, List[Dict[str, Any]]]:
        """Calculate weekly averages for each topic"""
        try:
            from datetime import datetime, timedelta
            
            weekly_trends = {}
            
            for topic, date_freq in freq_table.items():
                if not date_freq:
                    continue
                
                dates = sorted(date_freq.keys())
                if not dates:
                    continue
                
                # Group by weeks
                start_date = datetime.strptime(dates[0], "%Y-%m-%d")
                end_date = datetime.strptime(dates[-1], "%Y-%m-%d")
                
                weeks = []
                current_week_start = start_date
                
                while current_week_start <= end_date:
                    week_end = current_week_start + timedelta(days=6)
                    week_dates = [
                        d for d in dates 
                        if current_week_start <= datetime.strptime(d, "%Y-%m-%d") <= week_end
                    ]
                    
                    if week_dates:
                        week_total = sum(date_freq[d] for d in week_dates)
                        week_avg = week_total / len(week_dates)
                        
                        weeks.append({
                            "week_start": current_week_start.strftime("%Y-%m-%d"),
                            "week_end": week_end.strftime("%Y-%m-%d"),
                            "average": round(week_avg, 1),
                            "total": week_total
                        })
                    
                    current_week_start += timedelta(days=7)
                
                weekly_trends[topic] = weeks
            
            return weekly_trends
            
        except Exception as e:
            logger.error(f"Error calculating weekly averages: {str(e)}")
            return {}

    def _generate_actionable_recommendations(self, freq_table: Dict[str, Dict[str, int]],
                                            severity_scores: Dict[str, Dict[str, Any]],
                                            insights: Dict[str, Any],
                                            review_to_topics: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate actionable recommendations based on analysis"""
        try:
            recommendations = []
            
            # Get topics sorted by severity
            sorted_topics = sorted(
                severity_scores.items(),
                key=lambda x: x[1]["score"],
                reverse=True
            )
            
            # Top 5 most severe issues
            for i, (topic, severity_data) in enumerate(sorted_topics[:5], 1):
                classification = severity_data["classification"]
                score = severity_data["score"]
                avg_rating = severity_data["avg_rating"]
                total_reviews = severity_data["total_reviews"]
                
                # Calculate trend
                dates = sorted(freq_table.get(topic, {}).keys())
                if len(dates) >= 7:
                    recent_week = sum(freq_table[topic].get(d, 0) for d in dates[-7:])
                    previous_week = sum(freq_table[topic].get(d, 0) for d in dates[-14:-7])
                    
                    if previous_week > 0:
                        trend_pct = ((recent_week - previous_week) / previous_week) * 100
                    else:
                        trend_pct = 0
                    
                    trend_direction = "increasing" if trend_pct > 10 else ("decreasing" if trend_pct < -10 else "stable")
                else:
                    trend_pct = 0
                    trend_direction = "stable"
                
                # Generate recommendation text
                if classification == "CRITICAL":
                    action = "URGENT: Immediate attention required"
                    priority = 1
                elif classification == "HIGH":
                    action = "HIGH PRIORITY: Address within this sprint"
                    priority = 2
                elif classification == "MEDIUM":
                    action = "MEDIUM PRIORITY: Plan for upcoming sprint"
                    priority = 3
                else:
                    action = "LOW PRIORITY: Monitor and address in backlog"
                    priority = 4
                
                recommendation = {
                    "priority": priority,
                    "topic": topic,
                    "classification": classification,
                    "severity_score": score,
                    "action": action,
                    "details": f"{total_reviews} reviews (avg {avg_rating}★), {trend_direction} trend",
                    "trend_percentage": round(trend_pct, 1),
                    "affected_users": total_reviews,
                    "avg_rating": avg_rating
                }
                
                recommendations.append(recommendation)
            
            logger.info(f"Generated {len(recommendations)} actionable recommendations")
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return []
