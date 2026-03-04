
import pandas as pd
from collections import Counter
from src.kdi.export import export_to_excel
from src.kdi.constants import HTML_TEMPLATE, CHANNEL_MAP
from src.kdi.utils import get_priority_value

def negative_excel(df):
    try:
        negative_df = df[df['Sentiment'] == 'Negative'].copy()
        if negative_df.empty:
            return None, None
        print(negative_df.head(10))
        negative_excel_file, topic = export_to_excel(negative_df)
        return negative_excel_file, topic
    except:
        print("Error when export negative files")

def create_daily_report(df):

    df['PublishedDate'] = pd.to_datetime(df['PublishedDate'])
    start_date = df['PublishedDate'].min().strftime('%d.%m')
    end_date = df['PublishedDate'].max().strftime('%d.%m.%Y')
    end_date_only = df['PublishedDate'].max().strftime('%d.%m')
    all_records = df.to_dict(orient='records')
    topics = df['Topic'].dropna().unique()
    
    html_body = ""
    
    for topic in topics:
        sentiment_statements = {}
        sub_df = df[df['Topic'] == topic]
        topic_records = [record for record in all_records if record.get('Topic') == topic]
        total_mentions = len(topic_records)
        sentiments = [record['Sentiment'] for record in topic_records if record.get('Sentiment')]
        sentiment_counts = Counter(sentiments)
        positive_mentions = sentiment_counts.get('Positive', 0)
        neutral_mentions = sentiment_counts.get('Neutral', 0)
        negative_mentions = sentiment_counts.get('Negative', 0)

        channels = [record['Channel Group'] for record in topic_records if record.get('Channel Group')]
        channel_counts = Counter(channels)
        all_channels = list(channel_counts.keys())
        
        highlight_record = None
        all_content = [rec['Content'] for rec in topic_records if rec.get('Content')]
        if all_content:
            most_common_ = Counter(all_content).most_common(1)[0][0]
            highlight_record = next((rec for rec in topic_records if rec['Content'] == most_common_), None)
        else:
            highlight_record = None
     

        negative_records = [rec for rec in topic_records if rec.get('Sentiment') == 'Negative']
        counts = sub_df.groupby(['Channel Group','Sentiment','Type']).size()
        result = {}
        for (channel, sentiment, buzz_type), count in counts.items():
           result.setdefault(sentiment, {}).setdefault(channel, {})[buzz_type] = count
        for sentiment, channel_data in result.items():
            if sentiment not in ["Positive", "Negative"]:
                continue
            parts = []
            for channel, buzz_type_data in channel_data.items():
                buzz_type, count = get_priority_value(buzz_type_data)
                if buzz_type:
                    buzz_type = "bài đăng" if buzz_type == "topic" else "thảo luận"
                    if count > 0:
                        parts.append(f"{count:02d} {buzz_type} trên kênh {CHANNEL_MAP.get(channel, channel)}")
                    
            if parts:
                if sentiment.lower() == "negative":
                    sentiment_statements[sentiment] = f"Thảo luận tiêu cực ghi nhận " + ", ".join(parts)
                elif sentiment.lower() == "positive":
                    sentiment_statements[sentiment] = f"Thảo luận tích cực ghi nhận " + ", ".join(parts)

        html_body += f"""<h4>{topic}</h4>
        <p>- Tổng đề cập: <b>{total_mentions} lượt</b>. Trong đó có <b><span style='color:green;'>{positive_mentions} đề cập tích cực</span></b>, <b>{neutral_mentions} đề cập trung lập</b>, <b><span style='color:red;'>{negative_mentions} đề cập tiêu cực</span></b>.</p>
        <p>- Kênh {', kênh '.join([f"{CHANNEL_MAP.get(ch, ch)}: <b>{channel_counts.get(ch,0)} lượt</b>" for ch in all_channels])}.</p>
        """
        html_body += f"""<h5>1. Nội dung thảo luận</h5>"""
        sentiments = ["Positive", "Negative"]
        sentiment_html_lines = []
        for key in sentiments:
            sentence = sentiment_statements.get(key, "")
            if sentence:
                sentiment_html_lines.append(f"<p>- {sentence}.</p>")
        html_body += ''.join(sentiment_html_lines) if sentiment_html_lines else ""

        if highlight_record:
            truncate_words = highlight_record.get('Content', '').split()
            truncated_hightlight = ' '.join(truncate_words[:20])
            if len(truncate_words) > 20:
                truncated_hightlight += '...'
            html_body += f"""<p>- Trên {CHANNEL_MAP.get(highlight_record.get('Channel Group', ''), highlight_record.get('Channel Group', ''))}, nội dung thảo luận nổi bật ghi nhận tin <span style='color:purple;'>"{truncated_hightlight}"</span><a href='{highlight_record.get('UrlComment', '#')}'>[URL]</a>.</p>"""
        
        if negative_records:
            html_body += f"""<h5>2. Em gửi đính kèm là file tổng hợp tiêu cực từ ngày {start_date} - {end_date_only}.</h5>"""

        else:
            html_body += """<h5>2. Vì không ghi nhận tin tiêu cực nên báo cáo hôm nay không đính kèm file tổng hợp các tin tiêu cực.</h5>"""
        html_body += "<br>"

    html_report = HTML_TEMPLATE.format(body=html_body)

    return html_report.encode('utf-8')
