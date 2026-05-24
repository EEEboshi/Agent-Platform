"""
数据可视化工具
生成图表（折线图、柱状图、饼图、散点图等）
"""
from llama_index.core.tools import FunctionTool
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging
import json
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChartDataInput(BaseModel):
    """图表数据输入模型"""
    data: str = Field(description="数据（JSON 格式或 CSV 格式）")
    chart_type: str = Field(description="图表类型：line, bar, pie, scatter, area")
    title: str = Field(default="图表标题", description="图表标题")
    x_label: Optional[str] = Field(default=None, description="X 轴标签")
    y_label: Optional[str] = Field(default=None, description="Y 轴标签")
    output_file: str = Field(default="chart.png", description="输出文件路径")
    width: int = Field(default=800, description="图表宽度（像素）")
    height: int = Field(default=600, description="图表高度（像素）")


class ChartConfig:
    """图表配置"""
    
    CHART_TYPES = ['line', 'bar', 'pie', 'scatter', 'area', 'histogram', 'box']
    
    COLORS = [
        '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
        '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
    ]
    
    STYLES = {
        'default': 'default',
        'seaborn': 'seaborn-v0_8',
        'dark': 'dark_background',
        'classic': 'classic'
    }


def parse_data(data_str: str) -> tuple[List, List, Optional[List]]:
    """
    解析数据字符串
    返回：(x_labels, y_values, 可选的系列数据)
    """
    try:
        # 尝试 JSON 格式
        data = json.loads(data_str)
        
        if isinstance(data, dict):
            # 字典格式：{"label1": [1,2,3], "label2": [4,5,6]}
            labels = list(data.keys())
            values = list(data.values())
            if len(values) == 1:
                return labels, values[0], None
            else:
                return labels, values, None
                
        elif isinstance(data, list):
            # 列表格式
            if all(isinstance(item, dict) for item in data):
                # 对象列表：[{"x": "A", "y": 1}, {"x": "B", "y": 2}]
                x_labels = [item.get('x', f"Item {i}") for i, item in enumerate(data)]
                y_values = [item.get('y', 0) for item in data]
                return x_labels, y_values, None
            elif all(isinstance(item, (int, float)) for item in data):
                # 纯数字列表
                return [str(i) for i in range(len(data))], data, None
            else:
                # 二维列表：[["A", 1], ["B", 2]]
                x_labels = [str(item[0]) for item in data]
                y_values = [float(item[1]) for item in data]
                return x_labels, y_values, None
    except json.JSONDecodeError:
        pass
    
    # 尝试 CSV 格式
    try:
        lines = data_str.strip().split('\n')
        if len(lines) < 2:
            raise ValueError("CSV 数据至少需要表头和一行数据")
        
        # 读取表头
        headers = lines[0].split(',')
        
        # 读取数据
        x_labels = []
        y_values = []
        
        for line in lines[1:]:
            parts = line.split(',')
            if len(parts) >= 2:
                x_labels.append(parts[0].strip())
                y_values.append(float(parts[1].strip()))
        
        return x_labels, y_values, None
        
    except Exception as e:
        logger.error(f"数据解析失败：{e}")
        raise ValueError(f"无法解析数据格式：{str(e)}")


def create_chart(
    data: str,
    chart_type: str = "bar",
    title: str = "图表",
    x_label: Optional[str] = None,
    y_label: Optional[str] = None,
    output_file: str = "chart.png",
    width: int = 800,
    height: int = 600
) -> str:
    """
    创建图表。
    支持折线图、柱状图、饼图、散点图等
    
    Args:
        data: 数据（JSON 或 CSV 格式）
        chart_type: 图表类型（line/bar/pie/scatter/area）
        title: 图表标题
        x_label: X 轴标签
        y_label: Y 轴标签
        output_file: 输出文件路径
        width: 图表宽度
        height: 图表高度
        
    Returns:
        生成结果
    """
    try:
        import matplotlib.pyplot as plt
        import matplotlib
        matplotlib.use('Agg')  # 非交互式后端
        
        # 解析数据
        try:
            x_labels, y_values, series_data = parse_data(data)
        except Exception as e:
            return f"错误：数据解析失败 - {str(e)}"
        
        # 验证图表类型
        chart_type = chart_type.lower()
        if chart_type not in ChartConfig.CHART_TYPES:
            return f"错误：不支持的图表类型：{chart_type}，支持：{', '.join(ChartConfig.CHART_TYPES)}"
        
        # 创建图表
        fig, ax = plt.subplots(figsize=(width/100, height/100), dpi=100)
        
        if chart_type in ['line', 'bar', 'area', 'scatter']:
            if chart_type == 'line':
                ax.plot(x_labels, y_values, marker='o', linewidth=2, color=ChartConfig.COLORS[0])
            elif chart_type == 'bar':
                ax.bar(range(len(x_labels)), y_values, color=ChartConfig.COLORS[:len(x_labels)])
                ax.set_xticks(range(len(x_labels)))
                ax.set_xticklabels(x_labels, rotation=45, ha='right')
            elif chart_type == 'area':
                ax.fill_between(range(len(x_labels)), y_values, alpha=0.5, color=ChartConfig.COLORS[0])
                ax.plot(range(len(x_labels)), y_values, linewidth=2, color=ChartConfig.COLORS[0])
                ax.set_xticks(range(len(x_labels)))
                ax.set_xticklabels(x_labels, rotation=45, ha='right')
            elif chart_type == 'scatter':
                ax.scatter(range(len(x_labels)), y_values, s=100, alpha=0.6, color=ChartConfig.COLORS[0])
                ax.set_xticks(range(len(x_labels)))
                ax.set_xticklabels(x_labels, rotation=45, ha='right')
            
            # 设置标签
            if x_label:
                ax.set_xlabel(x_label)
            if y_label:
                ax.set_ylabel(y_label)
                
        elif chart_type == 'pie':
            # 饼图
            wedges, texts, autotexts = ax.pie(
                y_values,
                labels=x_labels,
                autopct='%1.1f%%',
                colors=ChartConfig.COLORS[:len(x_labels)],
                startangle=90
            )
            # 设置字体
            for text in texts:
                text.set_fontsize(8)
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
        
        # 设置标题
        ax.set_title(title, fontsize=14, fontweight='bold')
        
        # 网格线（非饼图）
        if chart_type != 'pie':
            ax.grid(True, alpha=0.3, linestyle='--')
        
        # 自动调整布局
        plt.tight_layout()
        
        # 确保输出目录存在
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 保存图表
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        plt.close()
        
        logger.info(f"图表已生成：{output_file}, 类型：{chart_type}")
        return f"图表已成功生成：{output_file}\n类型：{chart_type}\n数据点数：{len(y_values)}"
        
    except ImportError:
        return "错误：需要安装 matplotlib，请运行：pip install matplotlib"
    except Exception as e:
        logger.error(f"生成图表失败：{e}", exc_info=True)
        return f"生成失败：{str(e)}"


def create_multi_series_chart(
    data: str,
    chart_type: str = "line",
    title: str = "多系列图表",
    x_label: Optional[str] = None,
    y_label: Optional[str] = None,
    output_file: str = "multi_chart.png",
    width: int = 1000,
    height: int = 600
) -> str:
    """
    创建多系列图表。
    支持多个数据系列的对比
    
    Args:
        data: 数据（JSON 格式，每个键为一个系列）
        chart_type: 图表类型（line/bar/area）
        title: 图表标题
        x_label: X 轴标签
        y_label: Y 轴标签
        output_file: 输出文件路径
        width: 图表宽度
        height: 图表高度
        
    Returns:
        生成结果
    """
    try:
        import matplotlib.pyplot as plt
        import matplotlib
        matplotlib.use('Agg')
        
        # 解析数据
        try:
            data_dict = json.loads(data)
            if not isinstance(data_dict, dict):
                return "错误：多系列图表需要 JSON 对象格式，例如：{\"系列 1\": [1,2,3], \"系列 2\": [4,5,6]}"
        except json.JSONDecodeError:
            return "错误：数据必须是 JSON 格式"
        
        # 提取系列名称和数据
        series_names = list(data_dict.keys())
        series_data = list(data_dict.values())
        
        # 获取 X 轴标签（假设所有系列的 X 轴相同）
        if len(series_data) > 0 and isinstance(series_data[0], list):
            x_labels = [str(i) for i in range(len(series_data[0]))]
        else:
            x_labels = ["Category"]
        
        # 创建图表
        fig, ax = plt.subplots(figsize=(width/100, height/100), dpi=100)
        
        x_positions = range(len(x_labels))
        
        # 绘制每个系列
        for i, (name, values) in enumerate(zip(series_names, series_data)):
            if chart_type == 'line':
                ax.plot(x_labels, values, marker='o', linewidth=2, label=name, color=ChartConfig.COLORS[i % len(ChartConfig.COLORS)])
            elif chart_type == 'bar':
                offset = (i - len(series_names)/2) * 0.8 / len(series_names)
                bar_positions = [p + offset for p in x_positions]
                ax.bar(bar_positions, values, width=0.8/len(series_names), label=name, color=ChartConfig.COLORS[i % len(ChartConfig.COLORS)])
            elif chart_type == 'area':
                ax.fill_between(x_labels, values, alpha=0.3, label=name, color=ChartConfig.COLORS[i % len(ChartConfig.COLORS)])
        
        # 设置标签
        if x_label:
            ax.set_xlabel(x_label)
        if y_label:
            ax.set_ylabel(y_label)
        
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3, linestyle='--')
        
        if chart_type == 'bar':
            ax.set_xticks(x_positions)
            ax.set_xticklabels(x_labels, rotation=45, ha='right')
        
        plt.tight_layout()
        
        # 保存图表
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        plt.close()
        
        logger.info(f"多系列图表已生成：{output_file}, 系列数：{len(series_names)}")
        return f"多系列图表已成功生成：{output_file}\n类型：{chart_type}\n系列数：{len(series_names)}"
        
    except ImportError:
        return "错误：需要安装 matplotlib，请运行：pip install matplotlib"
    except Exception as e:
        logger.error(f"生成多系列图表失败：{e}", exc_info=True)
        return f"生成失败：{str(e)}"


def create_comparison_chart(
    data: str,
    title: str = "对比图表",
    output_file: str = "comparison_chart.png",
    width: int = 800,
    height: int = 600
) -> str:
    """
    创建对比柱状图（横向）。
    适合对比多个项目
    
    Args:
        data: 数据（JSON 或 CSV 格式）
        title: 图表标题
        output_file: 输出文件路径
        width: 图表宽度
        height: 图表高度
        
    Returns:
        生成结果
    """
    try:
        import matplotlib.pyplot as plt
        import matplotlib
        matplotlib.use('Agg')
        
        # 解析数据
        try:
            x_labels, y_values, _ = parse_data(data)
        except Exception as e:
            return f"错误：数据解析失败 - {str(e)}"
        
        # 创建横向柱状图
        fig, ax = plt.subplots(figsize=(width/100, height/100), dpi=100)
        
        y_positions = range(len(x_labels))
        colors = ChartConfig.COLORS[:len(x_labels)]
        
        bars = ax.barh(y_positions, y_values, color=colors)
        
        # 设置标签
        ax.set_yticks(y_positions)
        ax.set_yticklabels(x_labels)
        ax.set_xlabel("数值")
        ax.set_title(title, fontsize=14, fontweight='bold')
        
        # 在柱子上添加数值标签
        for i, (bar, value) in enumerate(zip(bars, y_values)):
            ax.text(value + max(y_values)*0.01, bar.get_y() + bar.get_height()/2, 
                   f'{value:.1f}', va='center', fontsize=9)
        
        ax.grid(True, alpha=0.3, axis='x', linestyle='--')
        plt.tight_layout()
        
        # 保存图表
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        plt.close()
        
        logger.info(f"对比图表已生成：{output_file}")
        return f"对比图表已成功生成：{output_file}\n项目数：{len(x_labels)}"
        
    except ImportError:
        return "错误：需要安装 matplotlib，请运行：pip install matplotlib"
    except Exception as e:
        logger.error(f"生成对比图表失败：{e}", exc_info=True)
        return f"生成失败：{str(e)}"


# 创建工具实例
chart_tool = FunctionTool.from_defaults(
    fn=create_chart,
    name="create_chart",
    description="创建图表（折线图、柱状图、饼图、散点图、面积图）",
    fn_schema=ChartDataInput
)

multi_series_chart_tool = FunctionTool.from_defaults(
    fn=create_multi_series_chart,
    name="create_multi_series_chart",
    description="创建多系列对比图表",
    fn_schema=ChartDataInput
)

comparison_chart_tool = FunctionTool.from_defaults(
    fn=create_comparison_chart,
    name="create_comparison_chart",
    description="创建横向对比柱状图",
    fn_schema=ChartDataInput
)

# 汇总所有可视化工具
VISUALIZATION_TOOLS = [
    chart_tool,
    multi_series_chart_tool,
    comparison_chart_tool
]
