from telegram import Update
from telegram.ext import ContextTypes
from config.config import Config
from utils.decorators import rate_limit, log_command
from utils.keyboards import BaseKeyboards
import aiohttp
from bs4 import BeautifulSoup

class SearchHandler:
    def __init__(self):
        self.session = None
        self.keyboards = BaseKeyboards()

    async def get_session(self):
        """Obtener sesión HTTP asincrόnica"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session

    @rate_limit(limit=3, window=60)  # Cambiado de time_window a window
    @log_command
    async def search(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Maneja el comando /search"""
        if not context.args:
            keyboard = self.keyboards.get_search_menu()
            await update.message.reply_text(
                "🔍 *Búsqueda de Información*\n\n"
                "Por favor, especifica qué quieres buscar:\n"
                "`/search término de búsqueda`\n\n"
                "También puedes usar los botones de abajo para opciones específicas.",
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            return

        query = ' '.join(context.args)
        await update.message.reply_text(
            "🔍 Buscando información...",
            parse_mode='Markdown'
        )

        try:
            results = await self.web_search(query)
            if results:
                response = "*Resultados de la búsqueda:*\n\n"
                for i, result in enumerate(results[:5], 1):
                    response += f"{i}. [{result['title']}]({result['url']})\n"
                    response += f"└ {result['description']}\n\n"
            else:
                response = "❌ No se encontraron resultados."

            keyboard = self.keyboards.get_search_results_menu(query)
            await update.message.reply_text(
                response,
                reply_markup=keyboard,
                parse_mode='Markdown',
                disable_web_page_preview=True
            )

        except Exception as e:
            await update.message.reply_text(
                f"❌ Error al realizar la búsqueda: {str(e)}",
                parse_mode='Markdown'
            )

    async def web_search(self, query: str) -> list:
        """Realizar búsqueda web sin API"""
        session = await self.get_session()
        results = []

        try:
            encoded_query = query.replace(' ', '+')
            url = f"https://html.duckduckgo.com/html/?q={encoded_query}"

            async with session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')

                    for result in soup.find_all('div', class_='result'):
                        title_elem = result.find('a', class_='result__a')
                        if title_elem:
                            title = title_elem.text.strip()
                            url = title_elem['href']
                            description = result.find('a', class_='result__snippet')
                            description = description.text.strip() if description else "Sin descripción"

                            results.append({
                                'title': title,
                                'url': url,
                                'description': description
                            })

                            if len(results) >= 5:
                                break

        except Exception as e:
            print(f"Error en web_search: {e}")

        return results

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Maneja los callbacks de los botones de búsqueda"""
        query = update.callback_query
        data = query.data

        if data.startswith('search_'):
            action = data.split('_')[1]

            if action == 'web':
                await query.message.reply_text(
                    "🌐 *Búsqueda Web*\n"
                    "Usa `/search término` para buscar en la web.",
                    parse_mode='Markdown'
                )
            elif action == 'wiki':
                await query.message.reply_text(
                    "📚 *Wikipedia*\n"
                    "Usa `/wiki término` para buscar en Wikipedia.",
                    parse_mode='Markdown'
                )

            await query.answer()

    @rate_limit(limit=2, window=60)  # Cambiado de time_window a window
    @log_command
    async def wiki(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Maneja el comando /wiki"""
        if not context.args:
            await update.message.reply_text(
                "❌ *Uso correcto:*\n"
                "/wiki término de búsqueda",
                parse_mode='Markdown'
            )
            return

        query = ' '.join(context.args)
        try:
            session = await self.get_session()
            url = "https://es.wikipedia.org/w/api.php"
            params = {
                "action": "query",
                "format": "json",
                "prop": "extracts|url",
                "exintro": True,
                "explaintext": True,
                "titles": query
            }

            async with session.get(url, params=params) as response:
                data = await response.json()
                pages = data["query"]["pages"]

                if "-1" in pages:
                    await update.message.reply_text(
                        "❌ No se encontró información en Wikipedia.",
                        parse_mode='Markdown'
                    )
                    return

                page = next(iter(pages.values()))
                title = page["title"]
                extract = page.get("extract", "No se encontró extracto")

                if len(extract) > 1000:
                    extract = extract[:997] + "..."

                response = f"*{title}*\n\n{extract}\n\n"
                response += f"🔗 [Leer más en Wikipedia](https://es.wikipedia.org/wiki/{query.replace(' ', '_')})"

                keyboard = self.keyboards.get_wiki_result_menu(query)
                await update.message.reply_text(
                    response,
                    reply_markup=keyboard,
                    parse_mode='Markdown',
                    disable_web_page_preview=True
                )

        except Exception as e:
            await update.message.reply_text(
                f"❌ Error al buscar en Wikipedia: {str(e)}",
                parse_mode='Markdown'
            )

    async def cleanup(self):
        """Limpia recursos"""
        if self.session:
            await self.session.close()