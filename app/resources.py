import streamlit as st
import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from googleapiclient.discovery import build
import time

# API Keys and Constants
GOOGLE_API_KEY = "AIzaSyBwqj7ev17iIACtZ9lGYjekpwwe15VdU2s"
CX = "57974449401e14b16"
YOUTUBE_API_KEY = "AIzaSyAAYW6fE95YLQ7KuHWBCUgOflLePBH3rIY"

# Function Definitions
def github_search(query, num_results=5):
    """Fetch popular GitHub repositories related to a query."""
    url = f"https://api.github.com/search/repositories?q={query}&sort=stars&order=desc"
    response = requests.get(url).json()
    repos = []
    for item in response.get("items", [])[:num_results]:
        repos.append({
            "name": item["name"],
            "url": item["html_url"],
            "stars": item["stargazers_count"],
            "owner": item.get("owner", {}).get("login", "Unknown"),
            "description": item.get("description", "No description available"),
            "language": item.get("language", "Unknown"),
            "updated_at": item.get("updated_at", "Unknown")
        })
    return repos

def get_trending_repos():
    """Fetch trending GitHub repositories."""
    url = "https://api.github.com/search/repositories?q=stars:>1000&sort=stars&order=desc"
    response = requests.get(url)
    data = response.json()
    repos = [
        {
            "name": repo["name"], 
            "url": repo["html_url"], 
            "stars": repo["stargazers_count"],
            "owner": repo.get("owner", {}).get("login", "Unknown"),
            "description": repo.get("description", "No description available"),
            "language": repo.get("language", "Unknown"),
            "updated_at": repo.get("updated_at", "Unknown")
        }
        for repo in data.get("items", [])[:5]
    ]
    return repos

def google_search(query, num_results=5):
    """Fetch Google search results and rank them using TF-IDF similarity."""
    url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={GOOGLE_API_KEY}&cx={CX}"
    response = requests.get(url).json()
    results = []
    for item in response.get("items", []):
        title = item.get("title", "")
        link = item.get("link", "")
        snippet = item.get("snippet", "")
        results.append({
            "title": title, 
            "link": link, 
            "snippet": snippet,
            "displayLink": item.get("displayLink", ""),
            "formattedUrl": item.get("formattedUrl", "")
        })
    return rank_results(query, results)

def rank_results(query, results):
    """Rank search results using TF-IDF similarity."""
    if not results:
        return []
    documents = [query] + [r["title"] + " " + r["snippet"] for r in results]
    vectorizer = TfidfVectorizer().fit_transform(documents)
    query_vector = vectorizer[0]  # First vector is the query
    doc_vectors = vectorizer[1:]  # Remaining vectors are results
    scores = cosine_similarity(query_vector, doc_vectors).flatten()
    ranked_results = sorted(zip(scores, results), reverse=True, key=lambda x: x[0])
    return [res for _, res in ranked_results]

def youtube_search(query, max_results=5):
    """Fetch YouTube videos for a given query."""
    try:
        youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
        request = youtube.search().list(
            q=query,
            part="snippet",
            maxResults=max_results,
            type="video"
        )
        response = request.execute()
        videos = []
        
        for item in response.get("items", []):
            # Safely extract values with error handling
            try:
                snippet = item.get("snippet", {})
                video_id = item.get("id", {}).get("videoId")
                
                # Skip items without a valid video ID
                if not video_id:
                    continue
                    
                title = snippet.get("title", "No title")
                url = f"https://www.youtube.com/watch?v={video_id}"
                channel = snippet.get("channelTitle", "Unknown channel")
                published_at = snippet.get("publishedAt", "Unknown date")
                
                # Safely get thumbnail - use default if not available
                thumbnails = snippet.get("thumbnails", {})
                thumbnail = thumbnails.get("medium", {}).get("url", "")
                if not thumbnail and "default" in thumbnails:
                    thumbnail = thumbnails["default"].get("url", "")
                
                description = snippet.get("description", "No description available")
                
                videos.append({
                    "title": title, 
                    "url": url,
                    "channel": channel,
                    "published_at": published_at,
                    "thumbnail": thumbnail,
                    "description": description
                })
            except Exception as e:
                st.error(f"Error processing video item: {str(e)}")
                continue
                
        return videos
    except Exception as e:
        st.error(f"YouTube API error: {str(e)}")
        return []
    
def get_top_videos():
    """Fetch trending YouTube videos on programming topics."""
    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q=best+Python+tutorial&type=video&maxResults=5&order=viewCount&key={YOUTUBE_API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        videos = [
            {
                "title": video["snippet"]["title"], 
                "url": f"https://www.youtube.com/watch?v={video['id']['videoId']}",
                "channel": video["snippet"]["channelTitle"],
                "published_at": video["snippet"]["publishedAt"],
                "thumbnail": video["snippet"]["thumbnails"]["medium"]["url"],
                "description": video["snippet"]["description"]
            }
            for video in data.get("items", [])
        ]
        return videos
    else:
        return []

def display_video_resource(video):
    """Display YouTube video resource with enhanced styling."""
    st.markdown(
        f"""
        <div class="resource-card category-video">
            <div class="resource-title">🎥 {video['title']}</div>
            <div class="metadata">Channel: {video['channel']}</div>
            <div class="metadata">Published: {video['published_at'].split('T')[0]}</div>
            <div class="metadata" style="margin-bottom: 10px;">
                <span class="tag">Video</span>
                <span class="tag">Educational</span>
                <span class="tag">Tutorial</span>
            </div>
            <div style="margin-bottom: 10px;">{video.get('description', '')[:150]}...</div>
            <a href="{video['url']}" target="_blank">
                <button style="background-color: #ff5252; color: white; border: none; padding: 5px 10px; border-radius: 5px; cursor: pointer;">
                    Watch Video
                </button>
            </a>
        </div>
        """,
        unsafe_allow_html=True
    )

def display_article_resource(article):
    """Display Google search result with enhanced styling."""
    st.markdown(
        f"""
        <div class="resource-card category-article">
            <div class="resource-title">📄 {article['title']}</div>
            <div class="metadata">Source: {article.get('displayLink', 'Unknown')}</div>
            <div class="metadata" style="margin-bottom: 10px;">
                <span class="tag">Article</span>
                <span class="tag">Web</span>
            </div>
            <div style="margin-bottom: 10px;">{article.get('snippet', '')}</div>
            <a href="{article['link']}" target="_blank">
                <button style="background-color: #4caf50; color: white; border: none; padding: 5px 10px; border-radius: 5px; cursor: pointer;">
                    Read Article
                </button>
            </a>
        </div>
        """,
        unsafe_allow_html=True
    )

def display_repo_resource(repo):
    """Display GitHub repository with enhanced styling."""
    st.markdown(
        f"""
        <div class="resource-card category-repo">
            <div class="resource-title">💻 {repo['name']}</div>
            <div class="metadata">Owner: {repo['owner']}</div>
            <div class="metadata">Stars: {repo['stars']} ⭐</div>
            <div class="metadata">Language: {repo.get('language', 'Unknown')}</div>
            <div class="metadata" style="margin-bottom: 10px;">
                <span class="tag">Repository</span>
                <span class="tag">Code</span>
                <span class="tag">{repo.get('language', 'Development')}</span>
            </div>
            <div style="margin-bottom: 10px;">{repo.get('description', 'No description available')}</div>
            <a href="{repo['url']}" target="_blank">
                <button style="background-color: #9c27b0; color: white; border: none; padding: 5px 10px; border-radius: 5px; cursor: pointer;">
                    View Repository
                </button>
            </a>
        </div>
        """,
        unsafe_allow_html=True
    )

def display_curated_resource(resource):
    """Display curated resource with enhanced styling."""
    colors = {
        "Article": "#4caf50",
        "Templates": "#ff9800",
        "Guide": "#2196f3",
        "Video": "#ff5252",
        "Repository": "#9c27b0"
    }
    color = colors.get(resource.get('type', 'Article'), "#0066cc")
    
    st.markdown(
        f"""
        <div class="resource-card" style="border-left-color: {color};">
            <div class="resource-title">📚 {resource['title']}</div>
            <div class="metadata">Type: {resource.get('type', 'Unknown')}</div>
            <div class="metadata">Category: {', '.join(resource.get('categories', ['General']))}</div>
            <div class="metadata" style="margin-bottom: 10px;">
                <span class="tag">{resource.get('type', 'Resource')}</span>
                {' '.join([f'<span class="tag">{cat}</span>' for cat in resource.get('categories', ['General'])])}
            </div>
            <div style="margin-bottom: 10px;">{resource.get('summary', 'No summary available')}</div>
            <a href="{resource['url']}" target="_blank">
                <button style="background-color: {color}; color: white; border: none; padding: 5px 10px; border-radius: 5px; cursor: pointer;">
                    View Resource
                </button>
            </a>
        </div>
        """,
        unsafe_allow_html=True
    )

def display_resources():
    """Main function to display resources."""
    # Sidebar
    with st.sidebar:
        st.image("https://via.placeholder.com/150x70.png?text=ResourceHub", width=150)
        st.title("Settings")
        
        # Dark Mode Toggle
        dark_mode = st.toggle("Dark Mode", value=False)
        if dark_mode:
            st.markdown("""
            <script>
                document.body.classList.add('dark-mode');
            </script>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <script>
                document.body.classList.remove('dark-mode');
            </script>
            """, unsafe_allow_html=True)
        
        # Filter options
        st.subheader("Filter Results")
        show_videos = st.checkbox("YouTube Videos", value=True)
        show_articles = st.checkbox("Articles", value=True)
        show_repos = st.checkbox("GitHub Repositories", value=True)
        
        max_results = st.slider("Results per category", min_value=1, max_value=10, value=5)
        
        st.markdown("---")
        st.subheader("About")
        st.info("""
        ResourceHub is an AI-powered recommendation engine that helps you discover the best learning resources across multiple platforms.
        
        Powered by: Google, YouTube, and GitHub APIs
        """)

    # Main content
    st.title("ResourceHub")
    st.subheader("Discover expert-curated learning resources")

    # Search bar with enhanced styling
    col1, col2 = st.columns([4, 1])
    with col1:
        query = st.text_input("What would you like to learn today?", placeholder="e.g., Machine Learning, JavaScript, Data Analysis...")
    with col2:
        search_button = st.button("Search", use_container_width=True)

    # Show loading animation
    if query and search_button:
        with st.spinner("Searching for the best resources..."):
            # Simulate loading for better UX
            time.sleep(1)
            
            # Create tabs for organized results
            tabs = st.tabs(["All Results", "Videos", "Articles", "Repositories"])
            
            # YouTube Results
            youtube_results = youtube_search(query, max_results) if show_videos else []
            
            # Google Search Results
            google_results = google_search(query, max_results) if show_articles else []
            
            # GitHub Repositories
            github_results = github_search(query, max_results) if show_repos else []
            
            # All Results Tab
            with tabs[0]:
                if not (youtube_results or google_results or github_results):
                    st.info("No results found. Try a different search term.")
                else:
                    col1, col2 = st.columns([1, 1])
                    count = 0
                    
                    # Mixed display of results
                    for i in range(max(len(youtube_results), len(google_results), len(github_results))):
                        if i < len(youtube_results) and show_videos:
                            with col1 if count % 2 == 0 else col2:
                                display_video_resource(youtube_results[i])
                            count += 1
                        
                        if i < len(google_results) and show_articles:
                            with col1 if count % 2 == 0 else col2:
                                display_article_resource(google_results[i])
                            count += 1
                        
                        if i < len(github_results) and show_repos:
                            with col1 if count % 2 == 0 else col2:
                                display_repo_resource(github_results[i])
                            count += 1
            
            # Videos Tab
            with tabs[1]:
                if not youtube_results:
                    st.info("No video results found. Try a different search term.")
                else:
                    col1, col2 = st.columns([1, 1])
                    for i, video in enumerate(youtube_results):
                        with col1 if i % 2 == 0 else col2:
                            display_video_resource(video)
            
            # Articles Tab
            with tabs[2]:
                if not google_results:
                    st.info("No article results found. Try a different search term.")
                else:
                    col1, col2 = st.columns([1, 1])
                    for i, article in enumerate(google_results):
                        with col1 if i % 2 == 0 else col2:
                            display_article_resource(article)
            
            # Repositories Tab
            with tabs[3]:
                if not github_results:
                    st.info("No repository results found. Try a different search term.")
                else:
                    col1, col2 = st.columns([1, 1])
                    for i, repo in enumerate(github_results):
                        with col1 if i % 2 == 0 else col2:
                            display_repo_resource(repo)

    # Featured Section (always visible)
    if not query or not search_button:
        st.markdown("### 🔥 Featured Resources")
        
        # Display featured content in a grid
        col1, col2 = st.columns([1, 1])
        
        curated_resources = [
            {
                "title": "The Ultimate Guide to Writing Cold Emails", 
                "url": "https://example.com/cold-emails", 
                "type": "Article",
                "categories": ["Career", "Communication"],
                "summary": "Learn how to craft compelling cold emails that get responses with this comprehensive guide."
            },
            {
                "title": "Professional Resume Templates 2025", 
                "url": "https://example.com/resume-templates", 
                "type": "Templates",
                "categories": ["Career", "Design"],
                "summary": "Download professionally designed resume templates that will help you stand out to recruiters."
            },
            {
                "title": "LinkedIn Profile Optimization Masterclass", 
                "url": "https://example.com/linkedin-guides", 
                "type": "Guide",
                "categories": ["Social Media", "Career"],
                "summary": "Boost your LinkedIn profile visibility and get more opportunities with these expert tips."
            },
            {
                "title": "Technical Interview Preparation Resources", 
                "url": "https://example.com/interview-prep", 
                "type": "Guide",
                "categories": ["Career", "Technology"],
                "summary": "Prepare for your technical interviews with coding exercises, system design problems, and behavioral questions."
            }
        ]
        
        with col1:
            display_curated_resource(curated_resources[0])
            display_curated_resource(curated_resources[2])
        
        with col2:
            display_curated_resource(curated_resources[1])
            display_curated_resource(curated_resources[3])
        
        # Trending Topics
        st.markdown("### 📈 Trending Topics")
        topic_cols = st.columns(5)
        topics = ["Machine Learning", "Web Development", "Data Science", "Mobile Apps", "Cloud Computing"]
        for i, topic in enumerate(topics):
            with topic_cols[i]:
                st.markdown(
                    f"""
                    <div style="background-color: #f0f4f8; padding: 15px; border-radius: 10px; text-align: center; cursor: pointer; height: 80px; display: flex; align-items: center; justify-content: center;">
                        <div>{topic}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style="display: flex; justify-content: space-between; padding: 10px 0;">
            <div>© 2025 ResourceHub. All rights reserved.</div>
            <div>
                <a href="#" style="margin-right: 15px; color: #0066cc; text-decoration: none;">Privacy Policy</a>
                <a href="#" style="margin-right: 15px; color: #0066cc; text-decoration: none;">Terms of Service</a>
                <a href="#" style="color: #0066cc; text-decoration: none;">Contact Us</a>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )