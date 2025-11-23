"""Library provider protocols for media libraries."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import ClassVar, Literal, Protocol, Self, TypeVar, runtime_checkable

from anibridge_providers.provider import BaseProvider

__all__ = [
    "ExternalId",
    "HistoryEntry",
    "IdNameSpace",
    "LibraryEntity",
    "LibraryEpisode",
    "LibraryMedia",
    "LibraryMovie",
    "LibraryProvider",
    "LibraryProviderT",
    "LibrarySeason",
    "LibrarySection",
    "LibraryShow",
    "MediaKind",
]


LibraryProviderT = TypeVar("LibraryProviderT", bound="LibraryProvider", covariant=True)


class MediaKind(StrEnum):
    """Supported high-level media kinds within a library provider."""

    MOVIE = "movie"
    SHOW = "show"
    SEASON = "season"
    EPISODE = "episode"


IdNameSpace = Literal["anidb", "anilist", "imdb", "mal", "plex", "tmdb", "tvdb"]


@dataclass(frozen=True, slots=True)
class ExternalId:
    """External identifier for a media item."""

    namespace: IdNameSpace
    value: str

    def __repr__(self) -> str:
        """Return a string representation of the external ID."""
        return f"{self.namespace}: {self.value}"


@runtime_checkable
class LibraryEntity(Protocol[LibraryProviderT]):
    """Base protocol for library entities."""

    key: str
    media_kind: MediaKind
    title: str

    def provider(self) -> LibraryProviderT:
        """Get the library provider this entity belongs to.

        Returns:
            LibraryProvider: The library provider.
        """
        ...

    def __hash__(self) -> int:
        """Compute the hash based on the entity's key."""
        return hash(f"{self.provider().NAMESPACE}:{self.__class__.__name__}:{self.key}")

    def __repr__(self) -> str:
        """Return a string representation of the library entity."""
        return f"<{self.__class__.__name__}:{self.key}:{self.title[:32]}>"


@runtime_checkable
class LibrarySection(LibraryEntity[LibraryProviderT], Protocol[LibraryProviderT]):
    """Represents a logical collection/section within the media library."""


@runtime_checkable
class LibraryMedia(LibraryEntity[LibraryProviderT], Protocol[LibraryProviderT]):
    """Base protocol for library items."""

    @property
    def on_watching(self) -> bool:
        """Check if the media item is on the user's current watching list.

        Determines whether the item is eligible for the current watching status.

        Returns:
            bool: True if currently watching, False otherwise.
        """
        ...

    @property
    def on_watchlist(self) -> bool:
        """Check if the media item is on the user's watchlist.

        Determines whether the item is eligible for the planning status.

        Returns:
            bool: True if on watchlist, False otherwise.
        """
        ...

    @property
    def poster_image(self) -> str | None:
        """Primary poster or cover image for the media item if available."""
        ...

    @property
    def user_rating(self) -> int | None:
        """Get the user rating for the media item.

        Returns:
            int | None: The user rating on a 0-100 scale, or None if not rated.
        """
        ...

    @property
    def view_count(self) -> int:
        """Get the view count for the media item.

        This includes views of child items as well.

        Returns:
            int: The number of times the item has been viewed.
        """
        ...

    async def history(self) -> Sequence[HistoryEntry]:
        """Get the user history entries for the media item.

        This includes view events for child items as well.

        Returns:
            Sequence[HistoryEntry]: User history entries.
        """
        ...

    def ids(self) -> Sequence[ExternalId]:
        """Get external identifiers associated with the media item.

        The ID namespace should be recognizable to AniBridge's mappings database.

        Returns:
            Sequence[ExternalId]: External identifiers.
        """
        ...

    async def review(self) -> str | None:
        """Get the user's review for the media item.

        Returns:
            str | None: The user's review text, or None if not reviewed.
        """
        ...

    def section(self) -> LibrarySection[LibraryProviderT]:
        """Get the library section this media item belongs to.

        Returns:
            LibrarySection: The parent library section.
        """
        ...


@runtime_checkable
class LibraryMovie(LibraryMedia[LibraryProviderT], Protocol[LibraryProviderT]):
    """Protocol for movie items in a media library."""


@runtime_checkable
class LibraryShow(LibraryMedia[LibraryProviderT], Protocol[LibraryProviderT]):
    """Protocol for episodic series items in a media library."""

    @property
    def ordering(self) -> Literal["tmdb", "tvdb", ""]:
        """Get the show's episode ordering method.

        Currently, only "tmdb" and "tvdb" are supported by the mappings database.

        Returns:
            Literal["tmdb", "tvdb", ""]: The episode ordering method.
        """
        ...

    def episodes(self) -> Sequence[LibraryEpisode[LibraryProviderT]]:
        """Get child episodes belonging to the show.

        Returns:
            Sequence[LibraryEpisode]: Child episodes.
        """
        ...

    def seasons(self) -> Sequence[LibrarySeason[LibraryProviderT]]:
        """Get child seasons belonging to the show.

        Returns:
            Sequence[LibrarySeason]: Child seasons.
        """
        ...


@runtime_checkable
class LibrarySeason(LibraryMedia[LibraryProviderT], Protocol[LibraryProviderT]):
    """Protocol for season items in a media library."""

    index: int

    def episodes(self) -> Sequence[LibraryEpisode[LibraryProviderT]]:
        """Get child episodes belonging to the season.

        Returns:
            Sequence[LibraryEpisode]: Child episodes.
        """
        ...

    def show(self) -> LibraryShow[LibraryProviderT]:
        """Get the parent show of the season.

        Returns:
            LibraryShow: The parent show.
        """
        ...

    def __repr__(self) -> str:
        """Return a string representation of the library entity."""
        return (
            f"<{self.__class__.__name__}:{self.key}:{self.show().title[:32]}:"
            f"S{self.index:02d}>"
        )


@runtime_checkable
class LibraryEpisode(LibraryMedia[LibraryProviderT], Protocol[LibraryProviderT]):
    """Protocol for episode items in a media library."""

    index: int
    season_index: int

    def season(self) -> LibrarySeason[LibraryProviderT]:
        """Get the parent season of the episode.

        Returns:
            LibrarySeason: The parent season.
        """
        ...

    def show(self) -> LibraryShow[LibraryProviderT]:
        """Get the parent show of the episode.

        Returns:
            LibraryShow: The parent show.
        """
        ...

    def __repr__(self) -> str:
        """Return a string representation of the library entity."""
        return (
            f"<{self.__class__.__name__}:{self.key}:{self.show().title[:32]}:"
            f"S{self.season_index:02d}E{self.index:02d}>"
        )


@dataclass(frozen=True, slots=True)
class HistoryEntry:
    """User history event for an item in the library."""

    library_key: str
    viewed_at: datetime  # Timestamps must be in UTC


class LibraryProvider(BaseProvider, Protocol):
    """Interface for a provider that exposes a user media library."""

    NAMESPACE: ClassVar[str]

    async def get_sections(self) -> Sequence[LibrarySection[Self]]:
        """Get all available library sections.

        Returns:
            Sequence[LibrarySection]: Available library sections.
        """
        ...

    async def list_items(
        self,
        section: LibrarySection[Self],
        *,
        min_last_modified: datetime | None = None,
        require_watched: bool = False,
        keys: Sequence[str] | None = None,
    ) -> Sequence[LibraryMedia[Self]]:
        """List items in a library section.

        Each item returned must belong to the specified section and meet the provided
        filtering criteria.

        Args:
            section (LibrarySection): The library section to list items from.
            min_last_modified (datetime | None): If provided, only items modified after
                this timestamp will be included.
            require_watched (bool): If True, only include items that have been marked as
                watched/viewed.
            keys (Sequence[str] | None): If provided, only include items whose keys are
                in this sequence.
        """
        ...
