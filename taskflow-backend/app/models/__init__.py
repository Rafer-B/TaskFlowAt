
"""Importa e publica os modelos para registo no metadata do SQLAlchemy."""

from app.models.user import User
from app.models.project import Project
from app.models.task import Task
from app.models.task_assignee import TaskAssignee
from app.models.project_member import ProjectMember
from app.models.task_work_log import TaskWorkLog, TaskWorkLogAttachment
from app.models.calendar_event import CalendarEvent
from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.password_reset_token import PasswordResetToken
from app.models.login_attempt import LoginAttempt
from app.models.notification import Notification
from app.models.task_history import TaskHistory
from app.models.email_login_code import EmailLoginCode
from app.models.two_factor_login_challenge import TwoFactorLoginChallenge

__all__ = [
    "User",
    "Project",
    "Task",
    "TaskAssignee",
    "ProjectMember",
    "TaskWorkLog",
    "TaskWorkLogAttachment",
    "CalendarEvent",
    "Team",
    "TeamMember",
    "PasswordResetToken",
    "LoginAttempt",
    "Notification",
    "TaskHistory",
    "EmailLoginCode",
    "TwoFactorLoginChallenge",
]
