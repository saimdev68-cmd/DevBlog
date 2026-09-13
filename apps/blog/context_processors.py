def reading_list_context(request):
    """Provides saved_post_ids and reading_list_count to all templates for authenticated readers."""
    if hasattr(request, 'user') and request.user.is_authenticated:
        saved_post_ids = set(request.user.read_later_entries.values_list('post_id', flat=True))
        return {
            'saved_post_ids': saved_post_ids,
            'reading_list_count': len(saved_post_ids),
        }
    return {
        'saved_post_ids': set(),
        'reading_list_count': 0,
    }
