CAMPAIGN_TEMPLATE = """
<h2>Campaign: '{campaign_title}'</h2>
<h3>Market: <a href={market_url}>{market_title}</a> </h3>
<h3>Run time: '{campaign_runtime}'</h3>
<br>
<h3>Items:</h3>
"""

CAMPAIGN_ITEM_TEMPLATE = """
<h4>Url: <a href={url}>{title}</a> </h4>
<h4>Available: {is_available} {is_notify_available}</h3>
<h4>On sale: {is_on_sale} {is_notify_sale}</h4>
<h4>Price: {price} {currency} <del>{before_price} {before_price_currency}</del></h4>
<br>
"""
