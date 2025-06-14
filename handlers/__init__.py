from aiogram import Router
from .common import common_router
from .questionnaire import router as questionnaire_router  # Correct import
from .menu import router as menu_router
from .edit_profile import router as edit_profile_menu

# Create main router
main_router = Router()

# Include routers - ORDER MATTERS!
main_router.include_router(common_router)
main_router.include_router(questionnaire_router)
main_router.include_router(menu_router)
main_router.include_router(edit_profile_menu)
# Export the main router
__all__ = ['main_router']