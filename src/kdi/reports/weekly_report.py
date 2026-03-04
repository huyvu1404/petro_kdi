import pandas as pd
from src.kdi.utils import get_priority_value
from src.kdi.constants import HTML_TEMPLATE, CHANNEL_MAP

def natural_join(names: list[str]) -> str:
    if not names:
        return ""
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return f"<span style='color: blue;'>{names[0]}</span> và <span style='color: purple;'>{names[1]}</span>"

    *others, last = names
    colored = ', '.join(f"<span style='color: purple;'>{n}</span>" for n in others)
    return f"{colored} và <span style='color: purple;'>{last}</span>"

def create_weekly_report(df: pd.DataFrame, last_week_df: pd.DataFrame) -> bytes:
    df['PublishedDate'] = pd.to_datetime(df['PublishedDate']).dt.normalize()
    start_date = df['PublishedDate'].min().strftime('%d.%m')
    end_date = df['PublishedDate'].max().strftime('%d.%m.%Y')

    html_body = ""
    
    sentiment_vi = {"Positive": "tích cực", "Negative": "tiêu cực", "Neutral": "trung lập"}

    for topic in df['Topic'].dropna().unique():
        sub_df = df[df['Topic'] == topic]
        last_week_mentions = len(last_week_df[last_week_df['Topic'] == topic])
        current_mentions = len(sub_df)

        if last_week_mentions:
            percent_change = (current_mentions - last_week_mentions) / last_week_mentions * 100
            change_str = f"{'tăng' if percent_change > 0 else 'giảm'} {abs(percent_change):.2f}% so với tuần trước"
        else:
            change_str = "không thay đổi so với tuần trước"

        sentiment_counts = sub_df['Sentiment'].value_counts().to_dict()
        positive, negative, neutral = (
            sentiment_counts.get("Positive", 0),
            sentiment_counts.get("Negative", 0),
            sentiment_counts.get("Neutral", 0)
        )

        counts = df.groupby(['Channel Group', 'Sentiment', 'Type']).size()
        sentiment_statements = {}

        for sentiment, channel_data in counts.groupby(level=1):
            if sentiment not in ("Positive", "Negative"):
                continue

            parts = []
            for channel, buzz_data in channel_data.groupby(level=0):
                buzz_type, count = get_priority_value(buzz_data.droplevel([0, 1]).to_dict())
                if count > 0:
                    buzz_label = "bài đăng" if buzz_type == "topic" else "thảo luận"
                    parts.append(f"{count:02d} {buzz_label} trên kênh {CHANNEL_MAP.get(channel, channel)}")

            if parts:
                label = "Thảo luận tích cực ghi nhận " if sentiment == "Positive" else "Thảo luận tiêu cực ghi nhận "
                sentiment_statements[sentiment] = label + ", ".join(parts)

        neutral_df = sub_df[sub_df["Sentiment"] == "Neutral"]
        if not neutral_df.empty:
            top_sites = neutral_df["SiteName"].dropna().value_counts().nlargest(3)
            if not top_sites.empty:
                site_part = natural_join(top_sites.index.tolist())
                url = neutral_df[neutral_df["SiteName"] == top_sites.index[0]].iloc[0]["UrlTopic"]
                sentiment_statements["Neutral"] = (
                    f"Các thảo luận trung lập nổi bật quảng bá {topic} "
                    f"<a href=\"{url}\">[URL]</a> được đăng tải liên tục trên các trang, "
                    f"{site_part} trong tuần qua."
                )

        empty_sentiments = [k for k in sentiment_vi if sentiment_counts.get(k, 0) == 0]
        if empty_sentiments:
            sentiment_statements["NoMentions"] = (
                "Không có thảo luận " +
                " và ".join(sentiment_vi[k] for k in empty_sentiments) +
                " nào được ghi nhận."
            )

        top_sources = []
        for channel, count in sub_df["New Channel"].value_counts().items():
            site_counts = sub_df.loc[sub_df["New Channel"] == channel, "SiteName"].dropna().value_counts()
            if not site_counts.empty:
                top_site = site_counts.idxmax()
                url = sub_df[sub_df["SiteName"] == top_site].iloc[0]["UrlTopic"]
                top_sources.append({
                    "Channel": channel, "TotalMentions": count, "SiteName": top_site, "URL": url
                })

        html_sources = (
            "<h5>Các lượt đăng bài và bình luận ghi nhận trên các nguồn tiêu biểu:</h5><ul>" +
            "".join(
                f"<li>{src['TotalMentions']} đề cập từ "
                f"{CHANNEL_MAP.get(src['Channel'], src['Channel'])}: "
                f"<a href=\"{src['URL']}\" style=\"color:#4da6ff;\">[{src['SiteName']}]</a></li>"
                for src in top_sources
            ) + "</ul>"
        )

        channel_group_counts = sub_df["Channel Group"].value_counts()
        channel_line = ', '.join(
            f"<b><span style='color: blue;'>kênh {CHANNEL_MAP.get(ch, ch)}:</span></b> "
            f"<b>{count} lượt</b>"
            for ch, count in channel_group_counts.items()
        )

        sentiment_html = ''.join(f"<p>- {s}.</p>" for s in sentiment_statements.values())
        html_body += f"""
            <h4>{topic}</h4>
            <p>- <b><span style="color: blue;">Tổng đề cập:</span> {current_mentions} lượt ({change_str})</b>.
               Trong đó có <b><span style="color: green;">{positive} tích cực</span></b>,
               <b>{neutral} trung lập</b>, <b><span style="color: red;">{negative} tiêu cực</span></b>.
            </p>
            <p>- {channel_line}.</p>
            <h5>Nội dung chính:</h5>
            {sentiment_html or "<p>- Không có thảo luận nào được ghi nhận.</p>"}
            {html_sources}
        """

    return HTML_TEMPLATE.format(body=html_body).encode("utf-8")
