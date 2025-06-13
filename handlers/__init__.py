from aiogram import Router
from .common import common_router
from .questionnaire import questionnaire_router

router = Router()
router.include_router(common_router)
router.include_router(questionnaire_router)
