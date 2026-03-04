CHANNEL_MAP = {
    "News": "Tin tức",
    "Facebook": "Facebook",
    "Forum": "Diễn đàn",
    "Blog": "Blog",
    "Instagram": "Instagram",
    "YouTube": "YouTube",
    "Twitter": "Twitter",
    "TikTok": "TikTok"
}

HTML_TEMPLATE = """
<html>
    <head>
        <meta charset="UTF-8">
        <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap" rel="stylesheet">
        <style>
            body {{
                font-family: 'Roboto', 'Arial', sans-serif;
                font-size: 15px;
                line-height: 1.6;
                color: #333333;
                background-color: #ffffff;
                margin: 20px;
            }}

            h1, h2, h3 {{
                font-family: 'Roboto', 'Georgia', serif;
                color: #222222;
                font-weight: 600;
            }}

            /* Style cho h4 */
            h4 {{
                font-family: 'Roboto', 'Arial', sans-serif;
                font-size: 17px;
                color: #4B0082;                
                font-weight: 600;
                border-left: 4px solid #4B0082; 
                padding-left: 8px;
                margin-top: 20px;
                margin-bottom: 10px;
            }}

            /* Style cho h5 */
            h5 {{
                font-family: 'Roboto', 'Arial', sans-serif;
                font-size: 16px;
                color: #555555;
                font-weight: 500;
                margin-top: 16px;
                margin-bottom: 6px;
            }}

            /* Bảng dữ liệu */
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 12px;
                font-size: 14px;
            }}

            th, td {{
                border: 1px solid #ccc;
                padding: 8px 10px;
            }}

            th {{
                background: #f4f4f4;
                font-weight: 600;
            }}

            /* Link trong báo cáo */
            a {{
                color: #0077cc;
                text-decoration: none;
            }}
            a:hover {{
                text-decoration: underline;
            }}

            /* Danh sách */
            ul {{
                padding-left: 20px;
            }}
            li {{
                margin-bottom: 5px;
            }}
        </style>
    </head>
    <body>
    {body}
    </body>
</html>
"""