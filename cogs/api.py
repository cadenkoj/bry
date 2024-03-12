import os
from discord.ext import commands, tasks
from quart import Quart, request, send_file

from constants import IS_PROD

class API(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.web_server.start()

    app = Quart(__name__)

    @app.route('/view')
    async def view():
        channel_id = request.args.get('channel_id')
        if not channel_id:
            return "Error: URL parameter is missing.", 400
    
        return await send_file(f"{os.getenv("RAILWAY_VOLUME_MOUNT_PATH")}/transcript-{channel_id}.html")
    
    @app.route('/download')
    async def download():
        channel_id = request.args.get('channel_id')
        if not channel_id:
            return "Error: URL parameter is missing.", 400

        return await send_file(f"{os.getenv("RAILWAY_VOLUME_MOUNT_PATH")}/transcript-{channel_id}.html", as_attachment=True)

    @tasks.loop()
    async def web_server(self):
        await self.app.run_task("0.0.0.0", os.getenv("PORT", 5000), not IS_PROD)

    @web_server.before_loop
    async def web_server_before_loop(self):
        await self.bot.wait_until_ready()

async def setup(bot: commands.Bot):
    await bot.add_cog(API(bot))