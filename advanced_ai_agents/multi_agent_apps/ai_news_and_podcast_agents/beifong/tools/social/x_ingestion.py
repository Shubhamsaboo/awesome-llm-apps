from tools.social.db import check_and_store_post, update_posts_with_analysis


class PostIngestor:
    def __init__(self, conn, analyze_posts=None, batch_size=5):
        if batch_size < 1:
            raise ValueError("batch_size must be positive")
        if analyze_posts is None:
            from tools.social.x_agent import analyze_posts_sentiment

            analyze_posts = analyze_posts_sentiment

        self.conn = conn
        self.analyze_posts = analyze_posts
        self.batch_size = batch_size
        self.seen_post_ids = set()
        self.analysis_queue = []
        self.post_count = 0

    def add(self, post_data):
        post_id = post_data.get("post_id")
        if not post_id or post_data.get("is_ad", False) or post_id in self.seen_post_ids:
            return False

        self.seen_post_ids.add(post_id)
        self.post_count += 1
        if check_and_store_post(self.conn, post_data) and post_data.get("post_text"):
            self.analysis_queue.append(post_data)

        if len(self.analysis_queue) >= self.batch_size:
            self._analyze(self.batch_size)
        return True

    def flush(self):
        while self.analysis_queue:
            self._analyze(len(self.analysis_queue))

    def _analyze(self, batch_length):
        batch = self.analysis_queue[:batch_length]
        del self.analysis_queue[:batch_length]
        try:
            analysis_results = self.analyze_posts(batch)
            update_posts_with_analysis(
                self.conn,
                [post["post_id"] for post in batch],
                analysis_results,
            )
        except Exception as error:
            raise RuntimeError("Post sentiment analysis failed. Stored posts will be retried on the next run.") from error
