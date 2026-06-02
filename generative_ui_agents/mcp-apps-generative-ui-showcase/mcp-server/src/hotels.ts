/**
 * Hotel booking data layer for the Hotel Booking demo.
 * Contains mock city/hotel data, room types, and booking logic.
 */

// Type definitions
export type RoomType = "standard" | "deluxe" | "suite" | "family" | "executive";
export type BedType = "king" | "queen" | "twin" | "double";
export type Amenity =
  | "wifi"
  | "pool"
  | "gym"
  | "spa"
  | "restaurant"
  | "parking"
  | "airConditioning"
  | "roomService"
  | "minibar"
  | "balcony";

/**
 * Represents a city destination.
 */
export interface City {
  name: string;
  country: string;
  timezone: string;
}

/**
 * Represents a room type in a hotel.
 */
export interface Room {
  id: string;
  type: RoomType;
  name: string;
  description: string;
  bedType: BedType;
  maxGuests: number;
  amenities: Amenity[];
  pricePerNight: number;
  available: number;
}

/**
 * Represents a hotel.
 */
export interface Hotel {
  id: string;
  name: string;
  stars: number; // 1-5
  address: string;
  neighborhood: string;
  city: string;
  amenities: Amenity[];
  rating: number; // 1-10 guest rating
  reviewCount: number;
  rooms: Room[];
}

/**
 * Represents a hotel search result.
 */
export interface HotelSearch {
  id: string;
  hotels: HotelWithPricing[];
  searchParams: {
    city: string;
    checkIn: string;
    checkOut: string;
    guests: number;
    rooms: number;
    nights: number;
  };
  selectedHotelId?: string;
  selectedRoomId?: string;
  selectedQuantity?: number;
}

/**
 * Hotel with calculated pricing for the search dates.
 */
export interface HotelWithPricing extends Hotel {
  pricePerNight: number; // Lowest room price
  totalPrice: number; // For all nights
}

/**
 * Guest information for booking.
 */
export interface Guest {
  name: string;
  email: string;
}

/**
 * Represents a completed hotel booking.
 */
export interface HotelBooking {
  confirmationNumber: string;
  hotel: Hotel;
  room: Room;
  roomQuantity: number;
  guests: Guest[];
  checkIn: string;
  checkOut: string;
  nights: number;
  totalPrice: number;
  specialRequests?: string;
  bookedAt: string;
}

/**
 * Mock city database with 10 destinations.
 */
const CITIES: City[] = [
  { name: "Paris", country: "France", timezone: "Europe/Paris" },
  { name: "New York", country: "USA", timezone: "America/New_York" },
  { name: "Tokyo", country: "Japan", timezone: "Asia/Tokyo" },
  { name: "London", country: "UK", timezone: "Europe/London" },
  { name: "Dubai", country: "UAE", timezone: "Asia/Dubai" },
  { name: "Singapore", country: "Singapore", timezone: "Asia/Singapore" },
  { name: "Barcelona", country: "Spain", timezone: "Europe/Madrid" },
  { name: "Sydney", country: "Australia", timezone: "Australia/Sydney" },
  { name: "Rome", country: "Italy", timezone: "Europe/Rome" },
  { name: "Amsterdam", country: "Netherlands", timezone: "Europe/Amsterdam" },
];

/**
 * Room type configurations.
 */
const ROOM_CONFIGS: Record<
  RoomType,
  {
    name: string;
    description: string;
    basePrice: number;
    maxGuests: number;
    amenities: Amenity[];
  }
> = {
  standard: {
    name: "Standard Room",
    description:
      "Comfortable room with essential amenities for a pleasant stay",
    basePrice: 120,
    maxGuests: 2,
    amenities: ["wifi", "airConditioning"],
  },
  deluxe: {
    name: "Deluxe Room",
    description: "Spacious room with premium amenities and city views",
    basePrice: 180,
    maxGuests: 2,
    amenities: ["wifi", "airConditioning", "minibar", "roomService"],
  },
  suite: {
    name: "Suite",
    description:
      "Luxurious suite with separate living area and premium services",
    basePrice: 350,
    maxGuests: 3,
    amenities: ["wifi", "airConditioning", "minibar", "roomService", "balcony"],
  },
  family: {
    name: "Family Room",
    description: "Large room ideal for families with extra beds and space",
    basePrice: 220,
    maxGuests: 4,
    amenities: ["wifi", "airConditioning", "minibar"],
  },
  executive: {
    name: "Executive Room",
    description:
      "Business-focused room with dedicated workspace and lounge access",
    basePrice: 250,
    maxGuests: 2,
    amenities: ["wifi", "airConditioning", "minibar", "roomService"],
  },
};

/**
 * Mock hotel database organized by city.
 */
const HOTELS: Record<string, Omit<Hotel, "id">[]> = {
  Paris: [
    {
      name: "Le Grand Paris",
      stars: 5,
      address: "15 Avenue des Champs-Élysées",
      neighborhood: "8th Arrondissement",
      city: "Paris",
      amenities: [
        "wifi",
        "pool",
        "gym",
        "spa",
        "restaurant",
        "parking",
        "roomService",
      ],
      rating: 9.2,
      reviewCount: 2847,
      rooms: [],
    },
    {
      name: "Hôtel Rivoli Boutique",
      stars: 4,
      address: "82 Rue de Rivoli",
      neighborhood: "1st Arrondissement",
      city: "Paris",
      amenities: ["wifi", "gym", "restaurant", "roomService"],
      rating: 8.7,
      reviewCount: 1523,
      rooms: [],
    },
    {
      name: "Montmartre Inn",
      stars: 3,
      address: "45 Rue Lepic",
      neighborhood: "Montmartre",
      city: "Paris",
      amenities: ["wifi", "restaurant"],
      rating: 8.1,
      reviewCount: 892,
      rooms: [],
    },
  ],
  "New York": [
    {
      name: "The Manhattan Grand",
      stars: 5,
      address: "789 Fifth Avenue",
      neighborhood: "Midtown",
      city: "New York",
      amenities: ["wifi", "gym", "spa", "restaurant", "parking", "roomService"],
      rating: 9.0,
      reviewCount: 4521,
      rooms: [],
    },
    {
      name: "SoHo Boutique Hotel",
      stars: 4,
      address: "120 Prince Street",
      neighborhood: "SoHo",
      city: "New York",
      amenities: ["wifi", "gym", "restaurant", "roomService"],
      rating: 8.5,
      reviewCount: 1876,
      rooms: [],
    },
    {
      name: "Brooklyn Bridge Inn",
      stars: 3,
      address: "55 Water Street",
      neighborhood: "DUMBO",
      city: "New York",
      amenities: ["wifi", "restaurant"],
      rating: 7.9,
      reviewCount: 743,
      rooms: [],
    },
  ],
  Tokyo: [
    {
      name: "Tokyo Imperial Palace Hotel",
      stars: 5,
      address: "1-1-1 Marunouchi, Chiyoda",
      neighborhood: "Chiyoda",
      city: "Tokyo",
      amenities: [
        "wifi",
        "pool",
        "gym",
        "spa",
        "restaurant",
        "parking",
        "roomService",
      ],
      rating: 9.4,
      reviewCount: 3892,
      rooms: [],
    },
    {
      name: "Shibuya Crossing Hotel",
      stars: 4,
      address: "2-21-1 Dogenzaka",
      neighborhood: "Shibuya",
      city: "Tokyo",
      amenities: ["wifi", "gym", "restaurant", "roomService"],
      rating: 8.6,
      reviewCount: 2134,
      rooms: [],
    },
    {
      name: "Asakusa Traditional Inn",
      stars: 3,
      address: "3-18-5 Asakusa",
      neighborhood: "Taito",
      city: "Tokyo",
      amenities: ["wifi", "restaurant"],
      rating: 8.3,
      reviewCount: 1267,
      rooms: [],
    },
  ],
  London: [
    {
      name: "The Royal Kensington",
      stars: 5,
      address: "100 Kensington High Street",
      neighborhood: "Kensington",
      city: "London",
      amenities: [
        "wifi",
        "pool",
        "gym",
        "spa",
        "restaurant",
        "parking",
        "roomService",
      ],
      rating: 9.1,
      reviewCount: 3456,
      rooms: [],
    },
    {
      name: "Covent Garden Hotel",
      stars: 4,
      address: "10 Monmouth Street",
      neighborhood: "West End",
      city: "London",
      amenities: ["wifi", "gym", "restaurant", "roomService"],
      rating: 8.8,
      reviewCount: 1987,
      rooms: [],
    },
    {
      name: "Camden Town Lodge",
      stars: 3,
      address: "45 Camden High Street",
      neighborhood: "Camden",
      city: "London",
      amenities: ["wifi", "restaurant"],
      rating: 7.8,
      reviewCount: 654,
      rooms: [],
    },
  ],
  Dubai: [
    {
      name: "Burj Al Arab Tower",
      stars: 5,
      address: "Jumeirah Beach Road",
      neighborhood: "Jumeirah",
      city: "Dubai",
      amenities: [
        "wifi",
        "pool",
        "gym",
        "spa",
        "restaurant",
        "parking",
        "roomService",
        "balcony",
      ],
      rating: 9.6,
      reviewCount: 5678,
      rooms: [],
    },
    {
      name: "Dubai Marina Suites",
      stars: 4,
      address: "Marina Walk",
      neighborhood: "Dubai Marina",
      city: "Dubai",
      amenities: ["wifi", "pool", "gym", "restaurant", "roomService"],
      rating: 8.9,
      reviewCount: 2345,
      rooms: [],
    },
    {
      name: "Old Town Hotel",
      stars: 3,
      address: "Al Fahidi Street",
      neighborhood: "Bur Dubai",
      city: "Dubai",
      amenities: ["wifi", "restaurant", "parking"],
      rating: 8.0,
      reviewCount: 876,
      rooms: [],
    },
  ],
  Singapore: [
    {
      name: "Marina Bay Sands",
      stars: 5,
      address: "10 Bayfront Avenue",
      neighborhood: "Marina Bay",
      city: "Singapore",
      amenities: [
        "wifi",
        "pool",
        "gym",
        "spa",
        "restaurant",
        "parking",
        "roomService",
      ],
      rating: 9.3,
      reviewCount: 4567,
      rooms: [],
    },
    {
      name: "Orchard Road Hotel",
      stars: 4,
      address: "270 Orchard Road",
      neighborhood: "Orchard",
      city: "Singapore",
      amenities: ["wifi", "pool", "gym", "restaurant", "roomService"],
      rating: 8.7,
      reviewCount: 2123,
      rooms: [],
    },
    {
      name: "Chinatown Heritage Inn",
      stars: 3,
      address: "36 Pagoda Street",
      neighborhood: "Chinatown",
      city: "Singapore",
      amenities: ["wifi", "restaurant"],
      rating: 8.2,
      reviewCount: 945,
      rooms: [],
    },
  ],
  Barcelona: [
    {
      name: "Casa Barcelona Grand",
      stars: 5,
      address: "Passeig de Gràcia 68",
      neighborhood: "Eixample",
      city: "Barcelona",
      amenities: ["wifi", "pool", "gym", "spa", "restaurant", "roomService"],
      rating: 9.0,
      reviewCount: 2987,
      rooms: [],
    },
    {
      name: "Gothic Quarter Hotel",
      stars: 4,
      address: "Carrer de Ferran 42",
      neighborhood: "Gothic Quarter",
      city: "Barcelona",
      amenities: ["wifi", "gym", "restaurant"],
      rating: 8.4,
      reviewCount: 1654,
      rooms: [],
    },
    {
      name: "Barceloneta Beach Inn",
      stars: 3,
      address: "Passeig Marítim 25",
      neighborhood: "Barceloneta",
      city: "Barcelona",
      amenities: ["wifi", "restaurant"],
      rating: 8.0,
      reviewCount: 789,
      rooms: [],
    },
  ],
  Sydney: [
    {
      name: "Sydney Harbour Grand",
      stars: 5,
      address: "1 Circular Quay",
      neighborhood: "The Rocks",
      city: "Sydney",
      amenities: [
        "wifi",
        "pool",
        "gym",
        "spa",
        "restaurant",
        "parking",
        "roomService",
      ],
      rating: 9.2,
      reviewCount: 3234,
      rooms: [],
    },
    {
      name: "Darling Harbour Hotel",
      stars: 4,
      address: "88 Harbour Street",
      neighborhood: "Darling Harbour",
      city: "Sydney",
      amenities: ["wifi", "pool", "gym", "restaurant", "roomService"],
      rating: 8.6,
      reviewCount: 1876,
      rooms: [],
    },
    {
      name: "Bondi Beach Lodge",
      stars: 3,
      address: "45 Campbell Parade",
      neighborhood: "Bondi",
      city: "Sydney",
      amenities: ["wifi", "restaurant"],
      rating: 8.1,
      reviewCount: 654,
      rooms: [],
    },
  ],
  Rome: [
    {
      name: "Hotel Roma Imperiale",
      stars: 5,
      address: "Via Veneto 125",
      neighborhood: "Via Veneto",
      city: "Rome",
      amenities: [
        "wifi",
        "pool",
        "gym",
        "spa",
        "restaurant",
        "parking",
        "roomService",
      ],
      rating: 9.1,
      reviewCount: 2876,
      rooms: [],
    },
    {
      name: "Trastevere Boutique Hotel",
      stars: 4,
      address: "Piazza di Santa Maria 15",
      neighborhood: "Trastevere",
      city: "Rome",
      amenities: ["wifi", "restaurant", "roomService"],
      rating: 8.8,
      reviewCount: 1543,
      rooms: [],
    },
    {
      name: "Colosseum View Inn",
      stars: 3,
      address: "Via dei Fori Imperiali 10",
      neighborhood: "Monti",
      city: "Rome",
      amenities: ["wifi", "restaurant"],
      rating: 8.2,
      reviewCount: 987,
      rooms: [],
    },
  ],
  Amsterdam: [
    {
      name: "Canal Ring Grand Hotel",
      stars: 5,
      address: "Herengracht 341",
      neighborhood: "Canal Ring",
      city: "Amsterdam",
      amenities: ["wifi", "gym", "spa", "restaurant", "roomService"],
      rating: 9.0,
      reviewCount: 2456,
      rooms: [],
    },
    {
      name: "Jordaan Boutique Hotel",
      stars: 4,
      address: "Prinsengracht 315",
      neighborhood: "Jordaan",
      city: "Amsterdam",
      amenities: ["wifi", "gym", "restaurant"],
      rating: 8.7,
      reviewCount: 1432,
      rooms: [],
    },
    {
      name: "Dam Square Inn",
      stars: 3,
      address: "Dam 27",
      neighborhood: "Centrum",
      city: "Amsterdam",
      amenities: ["wifi", "restaurant"],
      rating: 7.9,
      reviewCount: 765,
      rooms: [],
    },
  ],
};

// In-memory storage for hotel searches and bookings
export const hotelSearches: Map<string, HotelSearch> = new Map();
export const hotelBookings: Map<string, HotelBooking> = new Map();

/**
 * Get all available cities.
 */
export function getCities(): City[] {
  return CITIES.map((c) => ({ ...c }));
}

/**
 * Get city by name.
 */
export function getCityByName(name: string): City | undefined {
  return CITIES.find((c) => c.name.toLowerCase() === name.toLowerCase());
}

/**
 * Generate a unique search ID.
 */
function generateSearchId(): string {
  return `hotel-search-${Date.now()}-${Math.random().toString(36).substring(2, 8)}`;
}

/**
 * Generate a unique hotel ID.
 */
function generateHotelId(hotelName: string): string {
  const slug = hotelName.toLowerCase().replace(/[^a-z0-9]+/g, "-");
  return `hotel-${slug}-${Math.random().toString(36).substring(2, 6)}`;
}

/**
 * Generate a unique room ID.
 */
function generateRoomId(): string {
  return `room-${Math.random().toString(36).substring(2, 8)}`;
}

/**
 * Generate a confirmation number.
 */
function generateConfirmationNumber(): string {
  const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
  let result = "HTL";
  for (let i = 0; i < 6; i++) {
    result += chars[Math.floor(Math.random() * chars.length)];
  }
  return result;
}

/**
 * Calculate number of nights between two dates.
 */
function calculateNights(checkIn: string, checkOut: string): number {
  const start = new Date(checkIn);
  const end = new Date(checkOut);
  const diffTime = Math.abs(end.getTime() - start.getTime());
  return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
}

/**
 * Generate rooms for a hotel based on its star rating.
 */
function generateRooms(stars: number): Room[] {
  const rooms: Room[] = [];
  const bedTypes: BedType[] = ["king", "queen", "twin", "double"];

  // All hotels have standard rooms
  rooms.push({
    id: generateRoomId(),
    type: "standard",
    ...ROOM_CONFIGS.standard,
    bedType: bedTypes[Math.floor(Math.random() * bedTypes.length)],
    pricePerNight: Math.round(
      ROOM_CONFIGS.standard.basePrice * (0.8 + stars * 0.1) +
        Math.random() * 30,
    ),
    available: 5 + Math.floor(Math.random() * 10),
  });

  // 3+ star hotels have deluxe rooms
  if (stars >= 3) {
    rooms.push({
      id: generateRoomId(),
      type: "deluxe",
      ...ROOM_CONFIGS.deluxe,
      bedType: "king",
      pricePerNight: Math.round(
        ROOM_CONFIGS.deluxe.basePrice * (0.8 + stars * 0.1) +
          Math.random() * 50,
      ),
      available: 3 + Math.floor(Math.random() * 8),
    });
  }

  // 4+ star hotels have suites and executive rooms
  if (stars >= 4) {
    rooms.push({
      id: generateRoomId(),
      type: "suite",
      ...ROOM_CONFIGS.suite,
      bedType: "king",
      pricePerNight: Math.round(
        ROOM_CONFIGS.suite.basePrice * (0.8 + stars * 0.15) +
          Math.random() * 100,
      ),
      available: 2 + Math.floor(Math.random() * 5),
    });

    rooms.push({
      id: generateRoomId(),
      type: "executive",
      ...ROOM_CONFIGS.executive,
      bedType: "king",
      pricePerNight: Math.round(
        ROOM_CONFIGS.executive.basePrice * (0.8 + stars * 0.12) +
          Math.random() * 60,
      ),
      available: 2 + Math.floor(Math.random() * 6),
    });
  }

  // All hotels can have family rooms
  rooms.push({
    id: generateRoomId(),
    type: "family",
    ...ROOM_CONFIGS.family,
    bedType: "double",
    pricePerNight: Math.round(
      ROOM_CONFIGS.family.basePrice * (0.8 + stars * 0.1) + Math.random() * 40,
    ),
    available: 2 + Math.floor(Math.random() * 5),
  });

  return rooms;
}

/**
 * Search for hotels in a city.
 */
export function searchHotels(params: {
  city: string;
  checkIn: string;
  checkOut: string;
  guests: number;
  rooms?: number;
}): HotelSearch {
  const { city, checkIn, checkOut, guests, rooms = 1 } = params;

  const cityData = getCityByName(city);
  if (!cityData) {
    throw new Error(`City not found: ${city}`);
  }

  const nights = calculateNights(checkIn, checkOut);
  if (nights < 1) {
    throw new Error("Check-out date must be after check-in date");
  }

  const cityHotels = HOTELS[city];
  if (!cityHotels || cityHotels.length === 0) {
    throw new Error(`No hotels found in ${city}`);
  }

  const searchId = generateSearchId();

  // Build hotels with pricing and generated rooms
  const hotelsWithPricing: HotelWithPricing[] = cityHotels.map((hotel) => {
    const hotelWithId: Hotel = {
      ...hotel,
      id: generateHotelId(hotel.name),
      rooms: generateRooms(hotel.stars),
    };

    // Find lowest room price
    const lowestPrice = Math.min(
      ...hotelWithId.rooms.map((r) => r.pricePerNight),
    );

    return {
      ...hotelWithId,
      pricePerNight: lowestPrice,
      totalPrice: lowestPrice * nights * rooms,
    };
  });

  // Sort by rating (highest first)
  hotelsWithPricing.sort((a, b) => b.rating - a.rating);

  const search: HotelSearch = {
    id: searchId,
    hotels: hotelsWithPricing,
    searchParams: {
      city,
      checkIn,
      checkOut,
      guests,
      rooms,
      nights,
    },
  };

  // Store search for later reference
  hotelSearches.set(searchId, search);

  return search;
}

/**
 * Get hotel search by ID.
 */
export function getHotelSearch(searchId: string): HotelSearch | undefined {
  return hotelSearches.get(searchId);
}

/**
 * Select a hotel from search results.
 */
export function selectHotel(
  searchId: string,
  hotelId: string,
): { hotel: HotelWithPricing; rooms: Room[] } | undefined {
  const search = hotelSearches.get(searchId);
  if (!search) return undefined;

  const hotel = search.hotels.find((h) => h.id === hotelId);
  if (!hotel) return undefined;

  search.selectedHotelId = hotelId;

  return {
    hotel,
    rooms: hotel.rooms,
  };
}

/**
 * Select a room from a hotel.
 */
export function selectRoom(
  searchId: string,
  hotelId: string,
  roomId: string,
  quantity: number,
): { success: boolean; message: string; room?: Room; totalPrice?: number } {
  const search = hotelSearches.get(searchId);
  if (!search) {
    return { success: false, message: "Search session not found" };
  }

  const hotel = search.hotels.find((h) => h.id === hotelId);
  if (!hotel) {
    return { success: false, message: "Hotel not found" };
  }

  const room = hotel.rooms.find((r) => r.id === roomId);
  if (!room) {
    return { success: false, message: "Room type not found" };
  }

  if (quantity > room.available) {
    return {
      success: false,
      message: `Only ${room.available} rooms of this type available`,
    };
  }

  if (quantity * room.maxGuests < search.searchParams.guests) {
    return {
      success: false,
      message: `${quantity} ${room.name}(s) can only accommodate ${quantity * room.maxGuests} guests. You need rooms for ${search.searchParams.guests} guests.`,
    };
  }

  search.selectedHotelId = hotelId;
  search.selectedRoomId = roomId;
  search.selectedQuantity = quantity;

  const totalPrice = room.pricePerNight * search.searchParams.nights * quantity;

  return {
    success: true,
    message: `Selected ${quantity} ${room.name}(s) for ${search.searchParams.nights} night(s)`,
    room,
    totalPrice,
  };
}

/**
 * Create a hotel booking.
 */
export function createHotelBooking(
  searchId: string,
  guests: Guest[],
  specialRequests?: string,
): { success: boolean; message: string; booking?: HotelBooking } {
  const search = hotelSearches.get(searchId);
  if (!search) {
    return { success: false, message: "Search session not found" };
  }

  if (
    !search.selectedHotelId ||
    !search.selectedRoomId ||
    !search.selectedQuantity
  ) {
    return { success: false, message: "No room selected" };
  }

  const hotel = search.hotels.find((h) => h.id === search.selectedHotelId);
  if (!hotel) {
    return { success: false, message: "Hotel not found" };
  }

  const room = hotel.rooms.find((r) => r.id === search.selectedRoomId);
  if (!room) {
    return { success: false, message: "Room not found" };
  }

  if (guests.length === 0) {
    return { success: false, message: "At least one guest is required" };
  }

  const totalPrice =
    room.pricePerNight * search.searchParams.nights * search.selectedQuantity;
  const confirmationNumber = generateConfirmationNumber();

  const booking: HotelBooking = {
    confirmationNumber,
    hotel,
    room,
    roomQuantity: search.selectedQuantity,
    guests,
    checkIn: search.searchParams.checkIn,
    checkOut: search.searchParams.checkOut,
    nights: search.searchParams.nights,
    totalPrice,
    specialRequests,
    bookedAt: new Date().toISOString(),
  };

  // Store booking
  hotelBookings.set(confirmationNumber, booking);

  // Clear the search session
  hotelSearches.delete(searchId);

  return {
    success: true,
    message: `Booking confirmed! Your confirmation number is ${confirmationNumber}`,
    booking,
  };
}

/**
 * Get booking by confirmation number.
 */
export function getHotelBooking(
  confirmationNumber: string,
): HotelBooking | undefined {
  return hotelBookings.get(confirmationNumber);
}
