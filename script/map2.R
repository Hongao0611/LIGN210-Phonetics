# Load required packages
library(tidyverse)
library(sf)
library(ggplot2)

# 读取level-3数据
china_level3 <- st_read("gadm41_CHN_3.json")

# 过滤重庆数据
chongqing_counties <- china_level3 %>% 
  filter(NAME_1 == "Chongqing")

# 首先找出正确的区县名称字段
cat("数据字段名称:\n")
print(names(chongqing_counties))

# 查看可能的区县名称字段
if("NAME_3" %in% names(chongqing_counties)) {
  county_name_field <- "NAME_3"
  cat("使用NAME_3字段作为区县名称\n")
} else if("NAME_2" %in% names(chongqing_counties)) {
  county_name_field <- "NAME_2"
  cat("使用NAME_2字段作为区县名称\n")
} else {
  # 如果以上字段都不存在，使用第一个字符型字段
  char_cols <- sapply(chongqing_counties, is.character)
  if(any(char_cols)) {
    county_name_field <- names(chongqing_counties)[char_cols][1]
    cat("使用", county_name_field, "字段作为区县名称\n")
  } else {
    stop("未找到合适的区县名称字段")
  }
}

# 计算每个区县的中心点（用于放置空心圆点）
chongqing_centroids <- chongqing_counties %>%
  st_centroid() %>%
  mutate(
    centroid_x = st_coordinates(.)[,1],
    centroid_y = st_coordinates(.)[,2],
    # 添加标识是否为整体Chongqing标签的列
    is_chongqing_label = ifelse(.data[[county_name_field]] == "Chongqing", "Chongqing", "Other")
  )

# 创建无填充颜色的地图，添加空心圆点和区县标签
chongqing_map <- ggplot() +
  # 绘制区县边界，无填充颜色
  geom_sf(data = chongqing_counties, 
          fill = NA, 
          color = "#9c9c9c", 
          size = 0.5) +
  # 添加所有区县的空心圆点（其他区县半透明）
  geom_sf(data = chongqing_centroids %>% filter(is_chongqing_label == "Other"),
          aes(geometry = geometry),
          shape = 21,           # 空心圆点
          color = "#9c9c9c",
          fill = NA,            # 无填充
          size = 2,
          stroke = 1.5) +        # 半透明
  # 添加代表整体的Chongqing的红色双空心圆点
  geom_sf(data = chongqing_centroids %>% filter(is_chongqing_label == "Chongqing"),
          aes(geometry = geometry),
          shape = 21,           # 空心圆点
          color = "red",        # 红色边框
          fill = NA,            # 无填充
          size = 2,             # 更大的点
          stroke = 2.5,
          alpha = 0.8) +       
  # 添加其他区县标签（正常大小，半透明）
  geom_sf_text(data = chongqing_counties %>% 
                 filter(.data[[county_name_field]] != "Chongqing"),
               aes(label = .data[[county_name_field]]),
               size = 2.8,
               color = "#9c9c9c",
               check_overlap = FALSE) +   # 半透明标签
  # 添加代表整体的Chongqing标签（更大字体，红色）
  geom_sf_text(data = chongqing_counties %>% 
                 filter(.data[[county_name_field]] == "Chongqing"),
               aes(label = .data[[county_name_field]]),
               size = 6,        # 更大的字体
               color = "red",   # 红色字体
               check_overlap = FALSE,
               nudge_y = -0.07,
               alpha = 0.8) +
  theme_minimal() +
  labs(title = "Map of Chongqing",
       x = "Longitude", 
       y = "Latitude",
       caption = "Data source: GADM level-3") +
  theme(plot.title = element_text(hjust = 0.5, size = 16),
        plot.subtitle = element_text(hjust = 0.5, size = 12),
        axis.title.x = element_text(size = 12),
        axis.title.y = element_text(size = 12))

# 显示地图
print(chongqing_map)

# 保存地图
ggsave("chongqing_counties_outline.png", plot = chongqing_map, 
       width = 12, height = 10, dpi = 300)

# 打印区县列表
county_names <- unique(chongqing_counties[[county_name_field]])
cat("\n重庆市所有区县列表:\n")
cat("==================\n")
for(i in seq_along(county_names)) {
  if(county_names[i] == "Chongqing") {
    cat(sprintf("%2d. %s (整体标签)\n", i, county_names[i]))
  } else {
    cat(sprintf("%2d. %s\n", i, county_names[i]))
  }
}