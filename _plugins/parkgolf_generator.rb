require 'json'

module Jekyll
  class ParkgolfPageGenerator < Generator
    safe true
    priority :normal

    def generate(site)
      courses = load_json(site, '_rawdata/parkgolf.json')
      return if courses.empty?

      Jekyll.logger.info "ParkgolfGenerator:", "#{courses.size}개 파크골프장 페이지 생성 중..."

      courses.each do |c|
        next if c['slug'].to_s.strip.empty?
        site.pages << CoursePage.new(site, c)
      end

      by_region = courses.group_by { |c| c['doNm'] }
      by_region.each do |do_nm, do_courses|
        next if do_nm.to_s.strip.empty?
        site.pages << RegionPage.new(site, do_nm, do_courses)
      end

      site.pages << SearchIndexPage.new(site, courses)

      Jekyll.logger.info "ParkgolfGenerator:", "완료 (#{courses.size}개)"
    end

    private

    def load_json(site, path)
      file = File.join(site.source, path)
      return [] unless File.exist?(file)
      JSON.parse(File.read(file, encoding: 'utf-8'))
    rescue => e
      Jekyll.logger.warn "ParkgolfGenerator:", "#{path} 로드 실패: #{e.message}"
      []
    end
  end

  class CoursePage < Page
    def initialize(site, course)
      @site = site
      @base = site.source
      @dir  = "course/#{course['slug']}"
      @name = 'index.html'

      self.process(@name)
      self.read_yaml(File.join(@base, '_layouts'), 'course.html')
      data = course.dup
      data['courseName'] = data.delete('name')
      self.data.merge!(data)
      self.data['layout']      = 'course'
      self.data['title']       = build_title(course)
      self.data['description'] = build_desc(course)
    end

    private

    def build_title(c)
      loc = [c['doNm'], c['sigunguNm']].compact.join(' ')
      "#{c['name']} #{loc} 홀수 이용안내"
    end

    def build_desc(c)
      loc = [c['doNm'], c['sigunguNm']].compact.join(' ')
      parts = ["#{loc} #{c['name']}."]
      parts << "#{c['holes']}." if c['holes'].to_s.strip != ''
      parts << "운영기관: #{c['manager']}." if c['manager'].to_s.strip != ''
      parts << "이용요금: #{c['fee']}." if c['fee'].to_s.strip != ''
      parts.join(' ')[0, 155]
    end
  end

  class RegionPage < Page
    def initialize(site, do_nm, courses)
      @site = site
      @base = site.source
      @dir  = "region/#{do_nm}"
      @name = 'index.html'

      self.process(@name)
      self.read_yaml(File.join(@base, '_layouts'), 'region.html')
      self.data['layout']      = 'region'
      self.data['doNm']        = do_nm
      self.data['courses']     = courses
      self.data['title']       = "#{do_nm} 파크골프장 정보"
      self.data['description'] = "#{do_nm} 파크골프장 #{courses.size}개 목록. 위치, 홀 수, 운영기관을 확인하세요."
    end
  end

  class SearchIndexPage < Page
    def initialize(site, courses)
      @site = site
      @base = site.source
      @dir  = ''
      @name = 'search_index.json'

      self.process(@name)
      self.data = { 'layout' => nil, 'sitemap' => false }

      index = courses.map do |c|
        {
          'slug'      => c['slug'],
          'name'      => c['name'],
          'doNm'      => c['doNm'],
          'sigunguNm' => c['sigunguNm'],
          'holes'     => c['holes'],
          'address'   => c['address'],
        }
      end

      self.content = index.to_json
    end

    def output   = self.content
    def render(layouts, registers); end
  end
end
