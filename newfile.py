import discord
from discord.ext import commands
import datetime
import asyncio

# ==========================================
# ⚙️ الإعدادات الأساسية (يجب عليك تعبئتها بدقة)
# ==========================================
TOKEN = ""
OWNER_ID =   1231326854624055348
# D حسابك الشخصي
LOG_CHANNEL_ID =1481755695509405760
 # استبدله بـ ID روم "سجل العدالة"
ADMIN_CHANNEL_ID =1481755695509405759
# استبدله بـ ID روم "الإدارة اسرية"

# ==========================================
# 🛡️ تفعيل الصلاحيات (Intents)
# ==========================================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.moderation = True

# تعريف البوت وربطه بحسابك كـ "صاحب السيرفر"
bot = commands.Bot(command_prefix="!", intents=intents, owner_id=OWNER_ID)

# قاموس لتتبع عمليات الطرد والتبنيد (نظام فرامل الطوارئ)
mod_actions = {}

# ==========================================
# ⚖️ نظام طلبات الباند (الأزرار التفاعلية في خاصك)
# ==========================================
class BanRequestView(discord.ui.View):
    def __init__(self, target_user: discord.Member, moderator: discord.Member, reason: str, guild: discord.Guild):
        super().__init__(timeout=None) # الزر لن يختفي حتى تضغط عليه
        self.target_user = target_user
        self.moderator = moderator
        self.reason = reason
        self.guild = guild

    # زر الموافقة ✅
    @discord.ui.button(label="موافق (تبنيد)", style=discord.ButtonStyle.success, custom_id="approve_ban")
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != bot.owner_id:
            return await interaction.response.send_message("❌ هذا الزر لصاحب السيرفر فقط!", ephemeral=True)
        
        try:
            # تنفيذ الباند الفعلي
            await self.guild.ban(self.target_user, reason=f"طلب من {self.moderator.name} - السبب: {self.reason}")
            # تحديث الرسالة في خاصك
            await interaction.response.edit_message(content=f"✅ **تمت الموافقة** على تبنيد {self.target_user.mention} من قبلك.", view=None)
            
            # إرسال إشعار في سجل العدالة
            log_channel = self.guild.get_channel(LOG_CHANNEL_ID)
            if log_channel:
                await log_channel.send(f"🔨 **قرار إداري (مُصدق):** تمت الموافقة على تبنيد {self.target_user.mention}\n**السبب:** {self.reason}\n**بطلب من المشرف:** {self.moderator.mention}")
        except discord.Forbidden:
            await interaction.response.send_message("❌ البوت لا يملك صلاحية لتبنيد هذا الشخص (قد تكون رتبته أعلى من البوت).", ephemeral=True)

    # زر الرفض ❌
    @discord.ui.button(label="رفض الطلب", style=discord.ButtonStyle.danger, custom_id="reject_ban")
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != bot.owner_id:
            return await interaction.response.send_message("❌ هذا الزر لصاحب السيرفر فقط!", ephemeral=True)
        
        # تحديث الرسالة في خاصك
        await interaction.response.edit_message(content=f"❌ **تم رفض** طلب تبنيد {self.target_user.mention}.", view=None)
        
        # إبلاغ الإداري في الخاص بأنك رفضت طلبه
        try:
            await self.moderator.send(f"⚠️ **تنبيه:** صاحب السيرفر قام بـ **رفض** طلبك لتبنيد {self.target_user.mention} لعدم كفاية الأدلة أو لأسباب أخرى.")
        except:
            pass # في حال كان الإداري مقفل الخاص
        
        # إرسال إشعار في سجل العدالة
        log_channel = self.guild.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            await log_channel.send(f"🛡️ **شفافية:** تم **رفض** طلب المشرف {self.moderator.mention} لتبنيد {self.target_user.mention} من قبل صاحب السيرفر.")


# ==========================================
# 🚀 أحداث البوت عند التشغيل
# ==========================================
@bot.event
async def on_ready():
    print("="*40)
    print(f"✅ البوت متصل بنجاح: {bot.user.name}")
    print("🤖 [البذلة الآلية] جاهزة لتلقي أوامرك يا سيدي!")
    print("="*40)

# ==========================================
# 🤐 نظام منع التسريبات (حماية أسرار الإدارة)
# ==========================================
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    # الكلمات التي لو انكتبت في الشات العام تعتبر تسريب
    secret_keywords = ["قرار اداري", "تبنيد فلان", "سحب رتبة", "روم الادارة"]
    
    # التأكد أن الرسالة في السيرفر وليست في روم الإدارة السري
    if message.guild and message.channel.id != ADMIN_CHANNEL_ID:
        content_lower = message.content.lower()
        if any(keyword in content_lower for keyword in secret_keywords):
            # التحقق إذا كان الشخص إدارياً (لديه صلاحية الطرد مثلاً)
            if message.author.guild_permissions.kick_members:
                try:
                    await message.delete() # حذف الرسالة فوراً
                    
                    # إعطاء ميوت (Timeout) لمدة ساعة كعقوبة فورية
                    duration = datetime.timedelta(hours=1)
                    await message.author.timeout(duration, reason="النظام الآلي: تسريب معلومات إدارية")
                    
                    # إرسال إنذار لك في الخاص
                    owner = await bot.fetch_user(bot.owner_id)
                    await owner.send(f"🚨 **إنذار تسريب!** 🚨\nالإداري {message.author.mention} حاول تسريب كلام إداري في روم {message.channel.mention}.\n**الرسالة كانت:** `{message.content}`\n*الإجراء المتخذ: تم حذف الرسالة وإعطائه ميوت لمدة ساعة تلقائياً.*")
                except discord.Forbidden:
                    pass # تخطي إذا لم يكن للبوت صلاحية العقاب
                    
    await bot.process_commands(message) # ضروري جداً لكي تعمل باقي الأوامر

# ==========================================
# 🚨 نظام فرامل الطوارئ (3 بانات/طرد في دقيقة)
# ==========================================
@bot.event
async def on_audit_log_entry_create(entry: discord.AuditLogEntry):
    # نراقب فقط عمليات الطرد والتبنيد
    if entry.action in [discord.AuditLogAction.ban, discord.AuditLogAction.kick]:
        admin = entry.user
        if admin.bot or admin.id == bot.owner_id:
            return # استثناء البوت وأنت (صاحب السيرفر) من هذه الرقابة

        now = datetime.datetime.now(datetime.timezone.utc)
        
        if admin.id not in mod_actions:
            mod_actions[admin.id] = []
            
        # تسجيل وقت العملية
        mod_actions[admin.id].append(now)
        
        # تنظيف العمليات القديمة (نحتفظ فقط بما حدث في آخر 60 ثانية)
        mod_actions[admin.id] = [t for t in mod_actions[admin.id] if (now - t).total_seconds() <= 60]

        # إذا وصل العدد إلى 3 عمليات في دقيقة واحدة
        if len(mod_actions[admin.id]) >= 3:
            guild = entry.guild
            member_admin = guild.get_member(admin.id)
            
            if member_admin:
                try:
                    # جمع كل الرتب الإدارية التي يمتلكها وسحبها
                    roles_to_remove = [role for role in member_admin.roles if role.permissions.manage_messages or role.permissions.kick_members or role.permissions.ban_members or role.permissions.administrator]
                    await member_admin.remove_roles(*roles_to_remove, reason="فرامل الطوارئ الآلية: تجاوز حد التبنيد المسموح")
                    
                    # تنبيه عاجل لصاحب السيرفر
                    owner = await bot.fetch_user(bot.owner_id)
                    await owner.send(f"🚨 **طوارئ قصوى! حماية السيرفر تفعلت!** 🚨\nالإداري {member_admin.mention} قام بعمل 3 عمليات طرد/تبنيد في أقل من دقيقة!\n**تم سحب جميع رتبه الإدارية فوراً** وتجميده كإجراء احترازي. يرجى الدخول ومراجعة ما يحدث!")
                    
                    # تصفير العداد لهذا الإداري
                    mod_actions[admin.id] = []
                except discord.Forbidden:
                    owner = await bot.fetch_user(bot.owner_id)
                    await owner.send(f"⚠️ **تحذير خطير!** الإداري {member_admin.mention} يقوم بعمليات طرد عشوائية، ولكن رتبتي (البوت) أقل منه ولا أستطيع سحب رتبه! تدخّل فوراً!")

# ==========================================
# 📩 أمر تقديم طلب التبنيد (للإداريين)
# ==========================================
@bot.command(name="طلب_باند")
@commands.has_permissions(kick_members=True)
async def request_ban(ctx, member: discord.Member, *, reason: str):
    # منع المشرف من طلب تبنيد نفسه أو صاحب السيرفر
    if member.id == bot.owner_id or member == ctx.author:
        return await ctx.send("❌ لا يمكنك طلب تبنيد هذا الشخص.")
        
    # رسالة تطمين للمشرف تختفي بعد 5 ثواني
    await ctx.send("✅ تم إرسال طلب التبنيد لصاحب السيرفر سرياً للمراجعة.", delete_after=5)
    await ctx.message.delete() # حذف رسالة الطلب من الشات
    
    # إرسال الطلب مع الأزرار إلى خاصك أنت
    owner = await bot.fetch_user(bot.owner_id)
    view = BanRequestView(target_user=member, moderator=ctx.author, reason=reason, guild=ctx.guild)
    
    await owner.send(f"⚖️ **طلب تبنيد جديد ينتظر قرارك**\n**السيرفر:** {ctx.guild.name}\n**المشرف طالب الباند:** {ctx.author.mention}\n**العضو المخالف:** {member.mention}\n**السبب المكتوب:** `{reason}`\n\nما هو قرارك النهائي؟", view=view)

# ==========================================
# 👻 البذلة الآلية - التحكم الكامل (أنت تصبح البوت)
# ==========================================
@bot.command(name="تحدث")
@commands.is_owner() # حماية مطلقة: الكود لن يعمل إلا إذا كنت أنت المرسل
async def ghost_speak(ctx, channel_id: int, *, message_content: str):
    # إذا كتبت الأمر في سيرفر بالغلط، البوت يحذفه فوراً كي لا ينفضح أمرك
    if ctx.guild:
        try:
            await ctx.message.delete()
        except:
            pass
            
    # البحث عن الروم المطلوبة
    channel = bot.get_channel(channel_id)
    if channel:
        await channel.send(message_content) # البوت ينطق بكلامك
    else:
        # إذا أدخلت ID خطأ
        await ctx.author.send("❌ لم أتمكن من العثور على الروم. تأكد من نسخ الـ ID بشكل صحيح.")

# تشغيل البوت
bot.run(TOKEN)
