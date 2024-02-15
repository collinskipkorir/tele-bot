import logging, requests, json
import httpx
from telegram.ext import Application, InlineQueryHandler, ContextTypes, MessageHandler, filters, ConversationHandler, CommandHandler, CallbackContext, CallbackQueryHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton, InlineQueryResultArticle, InputTextMessageContent, InputFile
from CB import create_notion_page
from CB import update_notion_user_bank
from CB import get_user_property
from CB import check_user_registration
from CB import get_user_finance

#pip install python-telegram-bot requests httpx
# Create a single HTTP client session to be reused
http_client = httpx.AsyncClient(timeout=30.0)

bot_token = "5615171993:AAGS66tITdRycfLi8VtFfROAD8239lrKPvE"

url = f"https://api.telegram.org/bot{bot_token}/deleteMyCommands"
delcomd = requests.get(url)

def set_bot_commands():
    commands = [
        {"command": "menu", "description": "Home Menu"},
        {"command": "account", "description": "My Account"},
    ]

    url = f"https://api.telegram.org/bot{bot_token}/setMyCommands"
    data = {"commands": commands}

    setcomd = requests.post(url, json=data)

# Notion API 密钥和数据库 ID
api_key = "secret_lHfEsc4JQVwSt0kzVYvnLiEqLcJS0uftpOwSB1XRkvi"
database_id = "aa2f5dd9b83f4cd2a7d14c069039afc3"
headers = {
    "Authorization": "Bearer " + api_key,
    "Content-Type": "application/json",
    "Notion-Version": "2021-08-16"
}

CONFIRM_NAME, PHONE = range(2)

async def start(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    first_name = user.first_name
    last_name = user.last_name
    chat_id = update.message.chat_id

    context.user_data['chat_id'] = chat_id
    
    #check_user_registration
    is_registered = check_user_registration(context, database_id, headers, chat_id)
    if is_registered:
        # 用户已经注册，使用已注册的用户名字
        fullname = context.user_data['fullname']
        message = f"*Welcome back, {fullname}!*"
        await update.message.reply_text(text=message, parse_mode="Markdown", reply_markup=ReplyKeyboardRemove())

        await menu(update, context)
        return ConversationHandler.END
    else:
        # 用户未注册，使用 first_name 和 last_name 创建 fullname
        fullname = f"{first_name} {last_name}"
        context.user_data['fullname'] = fullname
        message = f"*Welcome to KristalLeatherCare!*\nMay I call you {fullname} ?\n\n💬 _Please enter your name below☺️_"
        keyboard = [[KeyboardButton(f"{fullname}")]]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text(text=message, parse_mode="Markdown", reply_markup=reply_markup)

    return CONFIRM_NAME

# 确认名字并提示输入电话号码
async def confirm_name(update: Update, context: CallbackContext) -> int:
    user_input = update.message.text

    # 检查用户输入是否等于按钮上显示的名字
    user = update.message.from_user
    first_name = user.first_name
    last_name = user.last_name

    fullname = f"{first_name} {last_name}"

    if user_input == fullname:
        # 用户点击按钮，使用 {first_name} 和 {last_name}
        context.user_data['fullname'] = fullname
    else:
        # 用户输入名字，直接使用用户输入的名字
        context.user_data['fullname'] = user_input
        
    # 提示用户输入电话号码
    await update.message.reply_text(f"Okay 👌 {context.user_data['fullname']}\n\nLet me assist you with a _quick registration_. \n\n💬 _Now, please enter your *WhatsApp number*_", parse_mode="Markdown", reply_markup=ReplyKeyboardRemove())
    return PHONE


async def get_phone(update: Update, context: CallbackContext) -> int:
    phone = update.message.text
    context.user_data['phone'] = phone
     
     #调用 create_notion_page 函数并传递所需的参数
    create_notion_page(context, database_id, headers)

    await update.message.reply_text(f"Congratulation 🎉 {context.user_data['fullname']}\nWhatsApp: {phone}\n Now you can start consignment with us.")
    
    context.user_data['state'] = 'MENU'
    await menu(update, context)  # 添加这一行以等待菜单消息被正确发送
    return ConversationHandler.END
    
async def menu(update: Update, context: CallbackContext) -> int:
    keyboard = [
        [InlineKeyboardButton("🚚 Start Selling 💰", url="https://kristalleathercare.com/consignment")],
        [InlineKeyboardButton("🔍 Set Your Price", switch_inline_query_current_chat="Set")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    set_bot_commands()
    await update.message.reply_text("欢迎到 Kristal 进行寄卖！\n第一次过来，可以先点击：*≪Start Selling≫*了解详情🔎\n\nWelcome to Consignment with Kristal!\nFor first time customer, please checkout *≪Start Selling≫* to learn more 🔎", reply_markup=reply_markup, parse_mode="Markdown")
    return ConversationHandler.END


SETBANK, BANK_NUMBER, BANK_COMPANY, UPLOAD_IC = range(4)

user_clicked_age = {}

# 在用户输入 /account 命令时，发送用户姓名和添加收款信息按钮
async def account(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    chat_id = update.message.chat_id
    
    await update.message.reply_text(f"Loading..", parse_mode="Markdown")
    get_user_property(context, database_id, headers, chat_id)
    #get_user_finance(context, headers, chat_id)

    # 构建消息文本，将 fullname 和 phone 插入消息中
    #print (f"{context.user_data.get('bank_company')}, {context.user_data.get('bank_number')}")
    #bank_number = context.user_data['bank_number']
    
    if context.user_data.get('bank_number'):
        message_account = f"👤 *My Account: *\n\n*Name:* _{context.user_data.get('fullname')}_\n*Phone:* _{context.user_data.get('phone')}_\n*Joined:* _{context.user_data.get('created_time')}_\n*Listing:* _{context.user_data.get('lst_item_qty')}_\n*Total Earning:* _{context.user_data.get('total_earning')}_\n*Receivable:* _{context.user_data.get('total_payable')}_\n\n_⬇️ Check your item listing below._"
        keyboard_account = [[
            InlineKeyboardButton("🔍 Selling", switch_inline_query_current_chat="Sell")
        ],
        [
            InlineKeyboardButton("🔍 Sold", switch_inline_query_current_chat="Sold")
        ],]
        markup_account = InlineKeyboardMarkup(keyboard_account)
        await update.message.reply_text(message_account, reply_markup=markup_account, parse_mode="Markdown")
        return ConversationHandler.END
    else:
        message_account = f"👤 *My Account: *\n\n*Name:* _{context.user_data.get('fullname')}_\n*Phone:* _{context.user_data.get('phone')}_\n*Joined:* _{context.user_data.get('created_time')}_\n*Listing:* _{context.user_data.get('lst_item_qty')}_\n*Total Earning:* _{context.user_data.get('total_earning')}_\n*Receivable:* _{context.user_data.get('total_payable')}_\n\n_⬇️ Set Your Bank To Get Money_"
        keyboard_account = [[InlineKeyboardButton("Set Account", callback_data="set_bank")]]
        markup_account = InlineKeyboardMarkup(keyboard_account)
        await update.message.reply_text(message_account, reply_markup=markup_account, parse_mode="Markdown")
    return SETBANK


# 创建获取银行信息的对话流程
async def set_bank(update: Update, context: CallbackContext) -> int:
    user = update.callback_query.from_user
    user_clicked_age[user.id] = True
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("💬 _Enter your Bank Account Number：_", parse_mode="Markdown")
    return BANK_NUMBER
    
async def collect_bank_number(update: Update, context: CallbackContext) -> int:
    bank_number = update.message.text
    context.user_data['bank_number'] = bank_number
    await update.message.reply_text(f"💬 _Enter your Bank Company Name：_", parse_mode="Markdown")

    return BANK_COMPANY

async def collect_bank_company(update: Update, context: CallbackContext) -> int:
    bank_company = update.message.text
    context.user_data['bank_company'] = bank_company
    await update.message.reply_text(f"🪪 _Upload your IC picture：_\n\n-Please ensure that the name on your Identity Card（IC） matches the name on your Bank Account to avoid any issues with receiving your funds.", parse_mode="Markdown")

    return UPLOAD_IC

async def collect_ic(update: Update, context: CallbackContext) -> int:
    ic = update.message.text
    context.user_data['ic'] = ic
    chat_id = update.message.chat_id
    ic_file_id = update.message.photo[-1].file_id
    file_info = await context.bot.get_file(ic_file_id)

    ic_photo_url = file_info.file_path
    context.user_data['ic'] = ic_photo_url

    await update.message.reply_text("Updating..")
    update_notion_user_bank(context, database_id, headers, chat_id)
    # 在这里，您可以处理用户提供的银行信息和上传的图片
    await update.message.reply_text("Account details received ✅")
    await account(update, context)
    return ConversationHandler.END



# Define the function to fetch user items based on chat ID
async def get_user_items_from_notion(chat_id):
    user_chat_id = str(chat_id)

    # Fetch the client data from Notion
    headers = {
        "Authorization": "Bearer secret_lHfEsc4JQVwSt0kzVYvnLiEqLcJS0uftpOwSB1XRkvi",
        "Notion-Version": "2022-06-28"
    }
    client_database_id = "aa2f5dd9b83f4cd2a7d14c069039afc3"  # Replace with the actual Client database ID
    client_url = f"https://api.notion.com/v1/databases/{client_database_id}/query"

    client_response = await http_client.post(client_url, headers=headers)
    client_data = client_response.json()

    user_items = []
    
    # Iterate through the client data to find the user's chat ID
    for client_page in client_data.get('results', []):
        if 'TGID' in client_page['properties']:
            tgid_property = client_page['properties']['TGID'].get('rich_text', [])
            if tgid_property and len(tgid_property) > 0:
                tgid_value = tgid_property[0].get('text', {}).get('content', '')
                if tgid_value == user_chat_id:
                    # Retrieve the relation to items for the user
                    item_relation = client_page['properties'].get('Item', {}).get('relation', [])

                    # Fetch the actual item pages related to the user
                    item_ids = [relation['id'] for relation in item_relation]
                    items = []

                    for item_id in item_ids:
                        item_url = f"https://api.notion.com/v1/pages/{item_id}"
                        item_response = await http_client.get(item_url, headers=headers)
                        item_data = item_response.json()

                        if 'Name' in item_data['properties'] and item_data['properties']['Name']['title']:
                            product_name = item_data['properties']['Name']['title'][0]['text']['content']

                            # Check if 'Suggestion Price' property exists
                            price_property = item_data['properties'].get('Suggestion Price', {})
                            product_price = str(price_property.get('number', 'Price not available'))
                            
                            customerprice_property = item_data['properties'].get('Customer Pricing', {})
                            sell_price = str(customerprice_property.get('number'))

                            # Retrieve the 'Status' property value or set a default value
                            status_property = item_data['properties'].get('Status', {})
                            status_name = status_property.get('status', {}).get('name', 'Status not available')

                            # Retrieve the 'Image' property URL or use a default image URL if not available
                            image_property = item_data['properties'].get('Image', {}).get('files', [])
                            if image_property:
                                 image_url = image_property[0].get('file', {}).get('url', 'http://kristalleathercare.com/wp-content/uploads/2024/02/kristal-logo-180.jpg')
                            else:
                                image_url = 'http://kristalleathercare.com/wp-content/uploads/2024/02/kristal-logo-180.jpg'

                            items.append({'name': product_name, 'item_id': item_id, 'sell_price': sell_price, 'price': product_price, 'status': status_name, 'image_url': image_url})

                    user_items.extend(items)

    return user_items


async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.inline_query.query.lower()

    if not query:
        return

    user_items = await get_user_items_from_notion(update.effective_user.id)
    results = []

    if "all" in query:
        # 显示全部产品
        filtered_items = user_items
        header_title = "📦 My Products:"
        header_desc = ""
    elif "set" in query:
        # 显示“status_property.get('status', {}).get('name'” 是in progress 的产品
        filtered_items = [item for item in user_items if item.get('status') == "In progress"]
        header_title = "🏷 Products in Progress:"
        header_desc = "⬇️ Choose item to set price ⬇️"
    elif "sell" in query:
        # 显示“status_property.get('status', {}).get('name'” 是selling 的产品
        filtered_items = [item for item in user_items if item.get('status') == "Selling"]
        header_title = "🔥 Selling Now！"
        header_desc = ""
    elif "sold" in query:
        # 显示“status_property.get('status', {}).get('name'” 是sold 的产品
        filtered_items = [item for item in user_items if item.get('status') == "Sold"]
        header_title = "✅ Sold Products:"
        header_desc = ""
    else:
        # 如果没有匹配的命令关键字，则显示默认结果
        filtered_items = []
        header_title = "Internet slow.. Please try again."
        header_desc = ""

    for index, item_info in enumerate(filtered_items):
        context.user_data['selected_item_id'] = item_info.get('item_id', 'Unknown ID')
        
        
        # 根据产品状态设置不同的描述文本
        if item_info.get('status') == "In progress":
            title_text = f"{item_info['name']} · RM{item_info['sell_price']}"
            description_text = "🔘 Set Price "
        elif item_info.get('status') == "Selling":
            title_text = f"{item_info['name']} · RM{item_info['sell_price']}"
            description_text = "📋 Item is listing."
        elif item_info.get('status') == "Sold":
            title_text = f"{item_info['name']} · RM{item_info['sell_price']}"
            description_text = "💰 Item sold."
        else:
            description_text = "No status information available."
        
        results.append(
            InlineQueryResultArticle(
                id=str(index),
                title=title_text,
                description=description_text,
                thumbnail_url=item_info['image_url'],
                thumbnail_width=100,  # 设置缩略图的宽度
                thumbnail_height=100,  # 设置缩略图的高度
                input_message_content=InputTextMessageContent(context.user_data['selected_item_id'])
            )
        )

    # 添加一个描述查询结果的消息
    results.insert(0, InlineQueryResultArticle(
        id="result_description",
        title=header_title,
        description=header_desc,
        input_message_content=InputTextMessageContent(header_title)
    ))

    await update.inline_query.answer(results or [InlineQueryResultArticle(id="no_results", title="No results found.")], cache_time=30)
    
PRICEHANDLER = 0

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    selected_item_id = update.message.text.strip()
    await update.message.reply_text(f"Loading..")
    # 使用 get_user_items_from_notion 获取的信息
    user_items = await get_user_items_from_notion(update.effective_user.id)

    # 查找选定项目的信息
    selected_item_info = None
    for item_info in user_items:
        if item_info.get('item_id') == selected_item_id:
            selected_item_info = item_info
            break

    if selected_item_info:
        item_name = selected_item_info.get('name', 'Unknown Name')
        item_price = selected_item_info.get('price', 'Unknown Price')
        item_image = selected_item_info.get('image_url')
        item_status = selected_item_info.get('status')
        item_unid = selected_item_info.get('item_id')
        sell_price = selected_item_info.get('sell_price')
        
        context.user_data['unname'] = item_name
        context.user_data['unid'] = item_unid
        
        photo_url = 'https://www.ouinolanguages.com/assets/French/vocab/8/images/pic7.jpg'

        # 发送包含更多信息的响应消息
        response_text = f"*[ {item_status} ]* _{item_name}_\n*Recommended Pricing*: _RM{item_price}_\n\n💬 Reply to set your price\n\n_-We suggest you set the recommended price._\n_-The final transaction price is expected to fluctuate around RM200._"
        #print(f"{selected_item_id}, {sell_price}, {item_name}")
        
        if not sell_price or sell_price.lower() == "none":
            # 如果 sell_price 为空，则进入 PRICEHANDLER
            #print("Entering PRICEHANDLER")
            #button_text = str(item_price)
            #button = KeyboardButton(button_text)
            #reply_markup = ReplyKeyboardMarkup([[button]], one_time_keyboard=True)
            keyboard = [[KeyboardButton(f"{item_price}")]]
            reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
            await update.message.reply_photo(photo=item_image, caption=response_text, reply_markup=reply_markup, parse_mode="Markdown") #, reply_markup=reply_markup
            return PRICEHANDLER
        else:
            #print("Not entering PRICEHANDLER")
            response_text_none = f"*[ {item_status} ]* _{item_name}_\n*Selling Price*: _RM{sell_price}_\n"
            await update.message.reply_photo(photo=item_image, caption=response_text_none, parse_mode="Markdown")
            return ConversationHandler.END



async def price_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    unprice = update.message.text.strip()

    # 记录用户输入的价格
    context.user_data['unprice'] = unprice
    unname = context.user_data.get('unname')
    
    # 更新数据库条目
    update_page_id = context.user_data.get('unid')  # 使用新创建的页面ID或现有页面ID
    update_url = f"https://api.notion.com/v1/pages/{update_page_id}"
    update_page_data = {
        "properties": {
            "Customer Pricing": {
                "number": float(context.user_data['unprice'])
            },# 更新其他属性...
        }
    }

    update_response = requests.patch(update_url, headers=headers, data=json.dumps(update_page_data))
    #print("页面更新成功", update_response.status_code)

    
    #print(f"{unname},{context.user_data.get('unid')}")

    # 回复用户确认
    await update.message.reply_text(f"✅ Price recorded for _[ {context.user_data.get('unname')} ]_ selling for *RM{unprice}*", parse_mode="Markdown", reply_markup=ReplyKeyboardRemove())
    await context.bot.send_message(-1002066833846, "🚨 有新产品可以上架了！赶快处理吧！！收到请点个👍 ..\n_[ 🔗 去notion上架](https://www.notion.so/ef989680cc4b40719ce6cd430529b771?v=71ff4e9b3acb4b2198676766faf02cb8&pvs=4)_", parse_mode="Markdown")

    return ConversationHandler.END  # 结束对话
    

def main() -> None:
    # 创建 Telegram Application 实例
    application = Application.builder().token(bot_token).build()

    # main.py 中的 ConversationHandler
    main_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start), CommandHandler("menu", menu)],
        states={
            CONFIRM_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_name)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
        },
        fallbacks=[],
    )

    # 添加 main.py 中的处理程序
    application.add_handler(main_conv_handler)
    
    # 创建一个新的ConversationHandler来管理获取银行信息的对话流程
    bank_info_handler = ConversationHandler(
        entry_points=[
            CommandHandler("account", account)  # 添加 /account 命令入口点
        ],
        states={
            SETBANK: [CallbackQueryHandler(set_bank)],
            BANK_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_bank_number)],
            BANK_COMPANY: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_bank_company)],
            UPLOAD_IC: [MessageHandler(filters.PHOTO & ~filters.COMMAND, collect_ic)],
        },
        fallbacks=[CommandHandler("account", account)]
    )

    # 添加 bank_info_handler 到 dispatcher
    application.add_handler(bank_info_handler)


    # bot.py 中的 ConversationHandler
    bot_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler)],
        states={
            PRICEHANDLER: [MessageHandler(filters.TEXT & ~filters.COMMAND, price_handler)],
        },
        fallbacks=[]
    )

    # 添加 bot.py 中的处理程序
    application.add_handler(InlineQueryHandler(inline_query))
    application.add_handler(bot_conv_handler)

    # 启动应用
    application.run_polling()

if __name__ == "__main__":
    main()
