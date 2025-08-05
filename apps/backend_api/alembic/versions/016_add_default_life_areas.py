"""Add default life areas

Revision ID: 016
Revises: 015
Create Date: 2024-01-11 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '016'
down_revision = '015'
branch_labels = None
depends_on = None


def upgrade():
    """Add default life areas to the database."""
    connection = op.get_bind()
    
    print("🔄 Adding default life areas...")
    
    # First, create a system user if it doesn't exist
    result = connection.execute(sa.text("SELECT COUNT(*) FROM users WHERE uid = 'system'"))
    if result.scalar() == 0:
        connection.execute(sa.text("""
            INSERT INTO users (uid, email) 
            VALUES ('system', 'system@selfos.local')
        """))
        print("✅ Created system user")
    else:
        print("✅ System user already exists")
    
    # Check if system life areas already exist
    result = connection.execute(sa.text("SELECT COUNT(*) FROM life_areas WHERE user_id = 'system'"))
    if result.scalar() == 0:
        print("🔄 Creating default life areas...")
        
        # Default life areas data
        life_areas_data = [
            ('Health & Fitness', 'Physical health, exercise, nutrition, and overall well-being', '#FF6B6B', 'favorite', '["health", "fitness", "exercise", "nutrition", "wellness", "medical", "sport"]', 1),
            ('Career & Work', 'Professional development, job satisfaction, and career growth', '#4ECDC4', 'work', '["career", "work", "job", "professional", "business", "office", "employment"]', 2),
            ('Relationships', 'Family, friends, romantic relationships, and social connections', '#FFE66D', 'family_restroom', '["family", "friends", "love", "social", "relationships", "partner", "community"]', 3),
            ('Personal Growth', 'Learning, self-improvement, education, and skill development', '#A8E6CF', 'school', '["growth", "learning", "education", "skills", "development", "improvement", "study"]', 4),
            ('Finance', 'Money management, savings, investments, and financial security', '#C7CEEA', 'attach_money', '["money", "finance", "budget", "savings", "investment", "wealth", "income"]', 5),
            ('Spirituality', 'Spiritual practice, mindfulness, meditation, and inner peace', '#FFDAB9', 'self_improvement', '["spiritual", "meditation", "mindfulness", "faith", "religion", "inner peace", "soul"]', 6),
            ('Fun & Recreation', 'Hobbies, entertainment, leisure activities, and enjoyment', '#B4A7D6', 'music_note', '["fun", "recreation", "hobbies", "entertainment", "leisure", "play", "relaxation"]', 7),
            ('Environment', 'Living space, home environment, and physical surroundings', '#D4A5A5', 'home', '["home", "environment", "living space", "organization", "comfort", "surroundings"]', 8),
        ]
        
        # Insert each life area
        now = datetime.utcnow()
        for name, description, color, icon, keywords, priority_order in life_areas_data:
            connection.execute(sa.text("""
                INSERT INTO life_areas (
                    user_id, name, description, color, icon, keywords,
                    weight, priority_order, is_custom, version, created_at, updated_at
                ) VALUES (
                    'system', :name, :description, :color, :icon, :keywords,
                    1.0, :priority_order, false, 1, :created_at, :updated_at
                )
            """), {
                'name': name,
                'description': description,
                'color': color,
                'icon': icon,
                'keywords': keywords,
                'priority_order': priority_order,
                'created_at': now,
                'updated_at': now,
            })
        
        print(f"✅ Created {len(life_areas_data)} default life areas")
    else:
        print("✅ Default life areas already exist")
    
    print("✅ Default life areas migration completed")


def downgrade():
    """Remove default life areas."""
    # Delete only the system life areas
    op.execute("""
        DELETE FROM life_areas 
        WHERE user_id = 'system' AND is_custom = false
    """)
    
    # Optionally remove the system user if no other data depends on it
    op.execute("""
        DELETE FROM users 
        WHERE uid = 'system' 
        AND NOT EXISTS (
            SELECT 1 FROM life_areas WHERE user_id = 'system'
        )
        AND NOT EXISTS (
            SELECT 1 FROM goals WHERE user_id = 'system'
        )
        AND NOT EXISTS (
            SELECT 1 FROM tasks WHERE user_id = 'system'
        )
        AND NOT EXISTS (
            SELECT 1 FROM projects WHERE user_id = 'system'
        )
    """)
    
    print("✅ Removed default life areas and system user")