lang = {
    'en': {
        'date_invalid': 'Input date is invalid',
        'date_not_next_month': 'Input date is not in next month',
        'no_record': 'No booking record found for you',
        'booking_date': 'Booking date',
        'failed_cancel': 'Failed to cancel the booking',
        'cancelled_successfully': 'Your booking on %s was cancelled.',
        'pls_input_date': 'Please input the date as MM-DD 3-25',
        'pls_input_time': 'Please input the time as hh:mm (24hour) 14:30',
        'pls_set_date_before_time': 'Please set date before set time',
        'booked_successfully': 'Thank you! Your booking was made successfully',
        'view_booking': 'View my booking',
        'cancel_booking': 'Cancel my booking',
        'make_booking': 'Make a booking',
        'hello': 'Hello',
        'confirm_cancel': 'Confirm to cancel your booking',
        'choose_cancel': 'Choose the one you want to cancel',
        'this_week': 'This week',
        'next_week': 'Next week',
        'week_after_next': 'Week after next',
        'week_after_next2': 'Week after next 2',
        'next_month': 'Next month',
        'pls_choose': 'Please choose',
        'pls_choose_language': 'Please choose your language',
        'your_booking_is': 'Hi %s, Your booking is %s.',
        'pls_check_chatbot': 'For more info pleaes check out our chatbot %s.',
    },
    'cn': {
        'date_invalid': '输入日期无效',
        'date_not_next_month': '输入的不是有效的下月日期',
        'no_record': '没有找到预订记录',
        'booking_date': '预订日期',
        'failed_cancel': '取消预定失败',
        'cancelled_successfully': '您已取消于%s的预定',
        'pls_input_date': '请输入日期, 如: 3-25',
        'pls_input_time': '请输入24小时制时间, 如: 14:30',
        'pls_set_date_before_time': '设置时间前请设置日期',
        'booked_successfully': '预定成功',
        'view_booking': '查看我的预定',
        'cancel_booking': '取消我的预定',
        'make_booking': '我要预定',
        'hello': '你好',
        'confirm_cancel': '确认取消预定',
        'choose_cancel': '选择您要取消的预定',
        'this_week': '本周',
        'next_week': '下周',
        'week_after_next': '下下周',
        'week_after_next2': '下下下周',
        'next_month': '下个雨',
        'pls_choose': '请选择',
        'pls_choose_language': '请选择您的语言',
        'your_booking_is': '%s您好, 您的预定是%s.',
        'pls_check_chatbot': '更多信息请查看我们的智能客服 %s.',
    },
}
import run

def trans(sender_id, name):
    locale = run.app.cache.get(sender_id + '_locale')
    if not locale:
        locale = 'cn'
    t = lang[locale]
    if name not in t:
        if name.index('_'):
            run.logger.warn('trans may get wrong name: ' + name)
    return t.get(name, name)
