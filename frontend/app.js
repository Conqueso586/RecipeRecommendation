// Recipe Finder React Application
const { useState, useEffect } = React;

const API_BASE_URL = 'http://localhost:5000/api';

// Difficulty indicator component
function DifficultyIndicator({ difficulty }) {
    const levels = { 'Easy': 1, 'Medium': 2, 'Hard': 3 };
    const level = levels[difficulty] || 1;
    
    return (
        <div className="difficulty-indicator">
            {[1, 2, 3].map(i => (
                <div 
                    key={i} 
                    className={`difficulty-dot ${i <= level ? 'active' : ''}`}
                />
            ))}
        </div>
    );
}

// Recipe card component
function RecipeCard({ recipe }) {
    return (
        <div className="recipe-card fade-in">
            <div className="cuisine-badge">{recipe.cuisine_type}</div>
            
            <div className="recipe-header">
                <h3 className="recipe-title">{recipe.name}</h3>
                {recipe.match_score && (
                    <div className="match-score">
                        {recipe.match_score}% Match
                    </div>
                )}
            </div>
            
            <div className="recipe-meta">
                <div className="meta-item">
                    <span>⏱️</span>
                    <span>{recipe.prep_time} min</span>
                </div>
                {recipe.cook_time > 0 && (
                    <div className="meta-item">
                        <span>🔥</span>
                        <span>{recipe.cook_time} min</span>
                    </div>
                )}
                <div className="meta-item">
                    <span>👥</span>
                    <span>{recipe.servings} servings</span>
                </div>
                <div className="meta-item">
                    <span>📊</span>
                    <DifficultyIndicator difficulty={recipe.difficulty} />
                    <span>{recipe.difficulty}</span>
                </div>
            </div>
            
            <div className="ingredients-list">
                <div className="ingredients-title">Ingredients:</div>
                <div className="ingredient-chips">
                    {recipe.ingredients}
                </div>
            </div>
            
            <div className="instructions-preview">
                {recipe.instructions}
            </div>
        </div>
    );
}

// Add recipe form component
function AddRecipeForm({ onRecipeAdded, onCancel }) {
    const [formData, setFormData] = useState({
        name: '',
        ingredients: [''],
        instructions: '',
        prep_time: 30,
        cook_time: 0,
        servings: 4,
        cuisine_type: 'General',
        difficulty: 'Medium'
    });
    const [submitting, setSubmitting] = useState(false);

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));
    };

    const handleIngredientChange = (index, value) => {
        const newIngredients = [...formData.ingredients];
        newIngredients[index] = value;
        setFormData(prev => ({
            ...prev,
            ingredients: newIngredients
        }));
    };

    const addIngredientField = () => {
        setFormData(prev => ({
            ...prev,
            ingredients: [...prev.ingredients, '']
        }));
    };

    const removeIngredientField = (index) => {
        const newIngredients = formData.ingredients.filter((_, i) => i !== index);
        setFormData(prev => ({
            ...prev,
            ingredients: newIngredients.length > 0 ? newIngredients : ['']
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setSubmitting(true);

        try {
            // Filter out empty ingredients
            const cleanedIngredients = formData.ingredients
                .map(ing => ing.trim())
                .filter(ing => ing.length > 0);

            if (cleanedIngredients.length === 0) {
                alert('Please add at least one ingredient.');
                return;
            }

            const recipeData = {
                ...formData,
                ingredients: cleanedIngredients,
                prep_time: parseInt(formData.prep_time),
                cook_time: parseInt(formData.cook_time),
                servings: parseInt(formData.servings)
            };

            const response = await fetch(`${API_BASE_URL}/recipes`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(recipeData),
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.details || error.error || 'Failed to create recipe');
            }

            const result = await response.json();
            alert('Recipe added successfully!');
            onRecipeAdded(result.recipe);
        } catch (error) {
            console.error('Error creating recipe:', error);
            alert(`Error creating recipe: ${error.message}`);
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <div className="search-section">
            <div className="form-section-header">
                <h2>Add New Recipe</h2>
                <button onClick={onCancel} className="cancel-btn">
                    Cancel
                </button>
            </div>
            
            <form onSubmit={handleSubmit}>
                <div className="form-group">
                    <label className="form-label required">Recipe Name</label>
                    <input
                        type="text"
                        name="name"
                        value={formData.name}
                        onChange={handleInputChange}
                        className="ingredient-input"
                        required
                        placeholder="Enter recipe name"
                    />
                </div>

                <div className="form-group">
                    <label className="form-label required">Ingredients</label>
                    {formData.ingredients.map((ingredient, index) => (
                        <div key={index} className="ingredient-row">
                            <input
                                type="text"
                                value={ingredient}
                                onChange={(e) => handleIngredientChange(index, e.target.value)}
                                className="ingredient-input"
                                placeholder="Enter ingredient"
                            />
                            {formData.ingredients.length > 1 && (
                                <button
                                    type="button"
                                    onClick={() => removeIngredientField(index)}
                                    className="remove-ingredient-btn"
                                >
                                    Remove
                                </button>
                            )}
                        </div>
                    ))}
                    <button
                        type="button"
                        onClick={addIngredientField}
                        className="add-ingredient-btn"
                    >
                        + Add Ingredient
                    </button>
                </div>

                <div className="form-group">
                    <label className="form-label required">Instructions</label>
                    <textarea
                        name="instructions"
                        value={formData.instructions}
                        onChange={handleInputChange}
                        className="ingredient-input textarea-input"
                        required
                        placeholder="Enter cooking instructions..."
                    />
                </div>

                <div className="form-grid">
                    <div className="form-group">
                        <label className="form-label">Prep Time (min)</label>
                        <input
                            type="number"
                            name="prep_time"
                            value={formData.prep_time}
                            onChange={handleInputChange}
                            className="ingredient-input"
                            min="1"
                        />
                    </div>

                    <div className="form-group">
                        <label className="form-label">Cook Time (min)</label>
                        <input
                            type="number"
                            name="cook_time"
                            value={formData.cook_time}
                            onChange={handleInputChange}
                            className="ingredient-input"
                            min="0"
                        />
                    </div>

                    <div className="form-group">
                        <label className="form-label">Servings</label>
                        <input
                            type="number"
                            name="servings"
                            value={formData.servings}
                            onChange={handleInputChange}
                            className="ingredient-input"
                            min="1"
                        />
                    </div>

                    <div className="form-group">
                        <label className="form-label">Cuisine Type</label>
                        <select
                            name="cuisine_type"
                            value={formData.cuisine_type}
                            onChange={handleInputChange}
                            className="ingredient-input"
                        >
                            <option value="General">General</option>
                            <option value="American">American</option>
                            <option value="Asian">Asian</option>
                            <option value="Italian">Italian</option>
                            <option value="Mexican">Mexican</option>
                            <option value="Mediterranean">Mediterranean</option>
                            <option value="Indian">Indian</option>
                            <option value="Thai">Thai</option>
                            <option value="French">French</option>
                            <option value="Chinese">Chinese</option>
                        </select>
                    </div>

                    <div className="form-group">
                        <label className="form-label">Difficulty</label>
                        <select
                            name="difficulty"
                            value={formData.difficulty}
                            onChange={handleInputChange}
                            className="ingredient-input"
                        >
                            <option value="Easy">Easy</option>
                            <option value="Medium">Medium</option>
                            <option value="Hard">Hard</option>
                        </select>
                    </div>
                </div>

                <button
                    type="submit"
                    disabled={submitting}
                    className="search-btn"
                >
                    {submitting ? 'Adding Recipe...' : 'Add Recipe'}
                </button>
            </form>
        </div>
    );
}

// Main application component
function App() {
    const [ingredients, setIngredients] = useState([]);
    const [currentIngredient, setCurrentIngredient] = useState('');
    const [recipes, setRecipes] = useState([]);
    const [loading, setLoading] = useState(false);
    const [hasSearched, setHasSearched] = useState(false);
    const [showAddForm, setShowAddForm] = useState(false);

    const addIngredient = () => {
        const ingredient = currentIngredient.trim().toLowerCase();
        if (ingredient && !ingredients.includes(ingredient)) {
            setIngredients([...ingredients, ingredient]);
            setCurrentIngredient('');
        }
    };

    const removeIngredient = (ingredientToRemove) => {
        setIngredients(ingredients.filter(ing => ing !== ingredientToRemove));
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            addIngredient();
        }
    };

    const searchRecipes = async () => {
        if (ingredients.length === 0) return;
        
        setLoading(true);
        setHasSearched(true);
        setShowAddForm(false);
        
        try {
            const response = await fetch(`${API_BASE_URL}/recipes/search`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ ingredients }),
            });
            
            if (!response.ok) {
                throw new Error('Failed to search recipes');
            }
            
            const data = await response.json();
            setRecipes(data.recipes || []);
        } catch (error) {
            console.error('Error searching recipes:', error);
            alert('Error searching recipes. Make sure the backend server is running on localhost:5000');
        } finally {
            setLoading(false);
        }
    };

    const loadAllRecipes = async () => {
        setLoading(true);
        setHasSearched(true);
        setShowAddForm(false);
        
        try {
            const response = await fetch(`${API_BASE_URL}/recipes`);
            if (!response.ok) {
                throw new Error('Failed to load recipes');
            }
            
            const data = await response.json();
            setRecipes(data.recipes || []);
        } catch (error) {
            console.error('Error loading recipes:', error);
            alert('Error loading recipes. Make sure the backend server is running on localhost:5000');
        } finally {
            setLoading(false);
        }
    };

    const handleRecipeAdded = (newRecipe) => {
        setRecipes(prev => [newRecipe, ...prev]);
        setShowAddForm(false);
        setHasSearched(true);
    };

    // Show add recipe form
    if (showAddForm) {
        return (
            <div className="container">
                <div className="header">
                    <h1>🍳 Recipe Finder</h1>
                    <p>Add your own delicious recipes to the collection!</p>
                </div>
                <AddRecipeForm 
                    onRecipeAdded={handleRecipeAdded}
                    onCancel={() => setShowAddForm(false)}
                />
            </div>
        );
    }

    // Main application view
    return (
        <div className="container">
            <div className="header">
                <h1>🍳 Recipe Finder</h1>
                <p>Find delicious recipes based on ingredients you have!</p>
            </div>
            
            <div className="search-section">
                <input
                    type="text"
                    value={currentIngredient}
                    onChange={(e) => setCurrentIngredient(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Enter an ingredient (e.g., chicken, rice, tomatoes)"
                    className="ingredient-input"
                />
                
                {ingredients.length > 0 && (
                    <div className="ingredient-tags">
                        {ingredients.map((ingredient, index) => (
                            <div key={index} className="ingredient-tag">
                                <span>{ingredient}</span>
                                <button
                                    onClick={() => removeIngredient(ingredient)}
                                    className="remove-tag"
                                >
                                    ×
                                </button>
                            </div>
                        ))}
                    </div>
                )}
                
                <div className="button-group">
                    <button
                        onClick={searchRecipes}
                        disabled={loading || ingredients.length === 0}
                        className="search-btn"
                    >
                        {loading ? 'Searching...' : 'Find Recipes'}
                    </button>
                    <button
                        onClick={loadAllRecipes}
                        disabled={loading}
                        className="search-btn"
                    >
                        Browse All Recipes
                    </button>
                    <button
                        onClick={() => setShowAddForm(true)}
                        disabled={loading}
                        className="search-btn add-recipe-btn"
                    >
                        + Add Recipe
                    </button>
                </div>
            </div>
            
            {loading && (
                <div className="loading">
                    🔍 Finding the perfect recipes for you...
                </div>
            )}
            
            {!loading && hasSearched && recipes.length === 0 && (
                <div className="no-results">
                    <p>😔 No recipes found with those ingredients.</p>
                    <p>Try adding different ingredients or browse all recipes!</p>
                </div>
            )}
            
            {!loading && recipes.length > 0 && (
                <div className="results-section">
                    {recipes.map((recipe) => (
                        <RecipeCard key={recipe.id} recipe={recipe} />
                    ))}
                </div>
            )}
        </div>
    );
}

// Initialize the React application
ReactDOM.render(<App />, document.getElementById('root'));