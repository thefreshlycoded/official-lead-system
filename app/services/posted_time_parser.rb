# frozen_string_literal: true

# Utility class for normalizing relative "posted" timestamps such as
# "2 minutes ago", "3 hours ago", "yesterday", etc. into an absolute
# time value.
class PostedTimeParser
  RELATIVE_REGEX = /\A(?<amount>an?|\d+)\s+(?<unit>[a-z]+)\s+ago\z/i

  UNIT_ALIASES = {
    'second' => :seconds,
    'seconds' => :seconds,
    'sec' => :seconds,
    'secs' => :seconds,
    'minute' => :minutes,
    'minutes' => :minutes,
    'min' => :minutes,
    'mins' => :minutes,
    'hour' => :hours,
    'hours' => :hours,
    'hr' => :hours,
    'hrs' => :hours,
    'day' => :days,
    'days' => :days,
    'week' => :weeks,
    'weeks' => :weeks,
    'month' => :months,
    'months' => :months,
    'year' => :years,
    'years' => :years
  }.freeze

  class << self
    # Converts a relative time expression (e.g. "2 minutes ago") to a
    # TimeWithZone instance using the supplied reference time.
    #
    # @param value [String, nil] raw value scraped for posted_time
    # @param reference_time [Time] point in time to subtract from (defaults to now)
    # @return [ActiveSupport::TimeWithZone, nil] parsed timestamp or nil if unrecognised
    def parse(value, reference_time: Time.zone.now)
      return nil if value.blank?

      normalized = value.to_s.strip
      normalized = strip_prefixes(normalized)
      normalized = strip_delimiters(normalized)
      lowercase = normalized.downcase

      return reference_time if %w[now just now just-now].include?(lowercase)
      return reference_time.beginning_of_day if lowercase == 'today'

      if lowercase == 'yesterday'
        return reference_time - 1.day
      elsif lowercase.start_with?('yesterday at ')
        return parse_yesterday_with_time(normalized, reference_time)
      end

      if (timestamp = parse_relative(lowercase, reference_time))
        return timestamp
      end

      parse_absolute(normalized)
    end

    private

    def strip_prefixes(value)
      value.sub(/\Aposted(?:\s+on)?\s*/i, '')
    end

    def strip_delimiters(value)
      value.split(/[\u2022|]/, 2).first.to_s.strip
    end

    def parse_relative(value, reference_time)
      match = RELATIVE_REGEX.match(value)
      return unless match

      amount = match[:amount].to_s.match?(/\Aan?\z/i) ? 1 : match[:amount].to_i
      unit_key = UNIT_ALIASES[match[:unit]]
      return unless unit_key

      reference_time - amount.public_send(unit_key)
    end

    def parse_yesterday_with_time(value, reference_time)
      time_fragment = value.split(/yesterday/i, 2).last.to_s.sub(/^at\s+/i, '').strip
      base = reference_time - 1.day
      return base if time_fragment.blank?

      parsed_time = Time.zone.parse("#{base.to_date} #{time_fragment}")
      parsed_time || base
    rescue ArgumentError
      base
    end

    def parse_absolute(value)
      Time.zone.parse(value)
    rescue ArgumentError, TypeError
      nil
    end
  end
end
