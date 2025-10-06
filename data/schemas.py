from marshmallow import Schema, fields, validate, validates, ValidationError, post_load

class RecipeSchema(Schema):
    """Schema for recipe validation and serialization."""
    
    id = fields.Integer(dump_only=True)
    name = fields.String(required=True, validate=validate.Length(min=1, max=200))
    ingredients = fields.List(fields.String(), required=True, validate=validate.Length(min=1))
    instructions = fields.String(required=True, validate=validate.Length(min=1))
    prep_time = fields.Integer(dump_default=30, validate=validate.Range(min=1, max=1440))  # 1 min to 24 hours
    cook_time = fields.Integer(dump_default=0, validate=validate.Range(min=0, max=1440))
    servings = fields.Integer(dump_default=4, validate=validate.Range(min=1, max=100))
    cuisine_type = fields.String(dump_default='General', validate=validate.Length(max=50))
    difficulty = fields.String(dump_default='Medium', validate=validate.OneOf(['Easy', 'Medium', 'Hard']))
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    
    @validates('ingredients')
    def validate_ingredients(self, value):
        """Validate that ingredients list is not empty and contains valid strings."""
        if not value:
            raise ValidationError('At least one ingredient is required.')
        
        for ingredient in value:
            if not ingredient or not ingredient.strip():
                raise ValidationError('Ingredients cannot be empty.')
            if len(ingredient.strip()) > 100:
                raise ValidationError('Ingredient names must be less than 100 characters.')
    
    @validates('name')
    def validate_name(self, value):
        """Validate recipe name."""
        if not value or not value.strip():
            raise ValidationError('Recipe name is required.')
    
    @validates('instructions')
    def validate_instructions(self, value):
        """Validate recipe instructions."""
        if not value or not value.strip():
            raise ValidationError('Instructions are required.')
class SearchSchema(Schema):
    """Schema for recipe search validation."""
    
    ingredients = fields.List(fields.String(), required=True, validate=validate.Length(min=1))
    cuisine_type = fields.String(dump_default=None)
    max_prep_time = fields.Integer(dump_default=None, validate=validate.Range(min=1))
    difficulty = fields.String(dump_default=None, validate=validate.OneOf(['Easy', 'Medium', 'Hard']))
    limit = fields.Integer(dump_default=10, validate=validate.Range(min=1, max=50))
    
    @validates('ingredients')
    def validate_search_ingredients(self, value):
        """Validate search ingredients."""
        if not value:
            raise ValidationError('At least one ingredient is required for search.')
        
        for ingredient in value:
            if not ingredient or not ingredient.strip():
                raise ValidationError('Search ingredients cannot be empty.')

# Schema instances for reuse
recipe_schema = RecipeSchema()
recipes_schema = RecipeSchema(many=True)
search_schema = SearchSchema()